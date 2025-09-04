import os
import json
import pickle
import numpy as np
import pyvista as pv
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from scipy import spatial
from logic.database.data_declarative_models import Patient, Visit, Manometry, BariumSwallow
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.reconstruction_service import ReconstructionService
from logic.services.barium_swallow_service import BariumSwallowFileService
from logic.services.manometry_service import ManometryFileService
from logic.services.endoscopy_service import EndoscopyFileService
from logic.services.endoflip_service import EndoflipFileService
from logic.visualization_data import VisualizationData
from logic.visit_data import VisitData
import config


class VTKHDFExporter:
    """
    VTKHDF exporter for 3D esophagus reconstructions with comprehensive ML attributes.

    This exporter creates VTKHDF files suitable for ML model validation with:
    - Complete metadata (patient, visit, acquisition parameters)
    - Per-slice or Per-vertex HRM pressure data
    - Per-vertex wall thickness
    - Per-vertex anatomical region classification (LES vs tubular)
    - HDF5 organization for efficient data access
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        max_pressure_frames: int = -1,
        pressure_export_mode: str = "per_vertex",
    ):
        """
        Initialize the VTKHDF Exporter.

        Args:
            db_session: Database session for metadata extraction
            max_pressure_frames: Maximum number of pressure frames to export (-1 for all)
        """
        self.db_session = db_session
        self.max_pressure_frames = max_pressure_frames
        # pressure_export_mode: 'per_vertex' | 'per_slice' | 'none'
        self.pressure_export_mode = pressure_export_mode

    def _sanitize_for_json(self, data: Any) -> Any:
        """
        Recursively sanitizes a data structure for JSON serialization.

        Args:
            data: The data to be sanitized, can be of any type.

        Returns:
            A sanitized version of the input data, ready for JSON serialization.
        """
        if isinstance(data, dict):
            return {key: self._sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._sanitize_for_json(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.generic):  # Catch any numpy scalar types
            return data.item()  # Convert numpy scalar to Python scalar
        elif hasattr(data, "tolist") and callable(
            getattr(data, "tolist")
        ):  # Handle numpy-like objects
            return data.tolist()
        elif isinstance(data, datetime):
            return data.isoformat()
        return data

    def export_visit_reconstructions(
        self,
        visit_data: VisitData,
        visit_name: str,
        output_directory: str,
        patient_id: Optional[str] = None,
        visit_id: Optional[int] = None,
        export_validation_attributes: bool = False,
        validation_attributes_format: str = "json",
    ) -> Dict[str, List[str]]:
        """
        Export all reconstructions from a visit to VTKHDF files.

        Args:
            visit_data: VisitData containing visualization data
            visit_name: Name identifier for the visit
            output_directory: Directory to save VTKHDF files
            patient_id: Patient ID for metadata
            visit_id: Visit ID for database metadata lookup
            export_validation_attributes: Whether to export validation attributes
            validation_attributes_format: Ignored (JSON is always used)

        Returns:
            Dictionary with 'mesh_files' and 'validation_files' lists
        """
        created_mesh_files = []
        created_validation_files = []

        # Minimal export log
        print(f"Starting VTKHDF export for visit: {visit_name}")

        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Extract database metadata if available
        metadata = self._extract_database_metadata(patient_id, visit_id)

        # Process each visualization in the visit
        for i, visualization_data in enumerate(visit_data.visualization_data_list):
            try:
                file_name = f"{visit_name}_{visualization_data.xray_minute}.vtkhdf"
                file_path = os.path.join(output_directory, file_name)

                success = self._export_single_reconstruction(
                    visualization_data, file_path, metadata, visit_name, i
                )

                if success:
                    created_mesh_files.append(file_path)
                    if export_validation_attributes:
                        validation_file_path = self._export_validation_attributes(
                            visualization_data,
                            visit_name,
                            output_directory,
                            metadata,
                            validation_attributes_format,
                        )
                        if validation_file_path:
                            created_validation_files.append(validation_file_path)

            except Exception as e:
                print(f"Error exporting visualization {i}: {str(e)}")
                continue

        # Export summary
        total_visualizations = len(visit_data.visualization_data_list)
        successful_exports = len(created_mesh_files)
        failed_exports = total_visualizations - successful_exports

        print(
            f"Export summary for visit '{visit_name}': "
            f"{successful_exports}/{total_visualizations} meshes, "
            f"{len(created_validation_files)} validation files"
        )

        return {"mesh_files": created_mesh_files, "validation_files": created_validation_files}

    def _validate_database_connection(self) -> bool:
        """
        Validate if database connection is active and accessible.

        Returns:
            bool: True if database connection is valid, False otherwise
        """
        if not self.db_session:
            print("No database session provided - patient and clinical data will not be exported")
            return False

        try:
            # Test database connection with a simple query
            self.db_session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            print(
                "This may be due to SQLAlchemy version compatibility or database connectivity issues"
            )
            print("Patient and clinical data will not be exported")
            return False

    def _log_export_parameters(
        self, patient_id: Optional[str], visit_id: Optional[int], visit_name: str
    ):
        """Log export parameters for debugging."""
        print("Export Parameters:")
        print(f"  Patient ID: {patient_id if patient_id else 'None'}")
        print(f"  Visit ID: {visit_id if visit_id else 'None'}")
        print(f"  Visit Name: {visit_name}")
        print(f"  Database Session: {'Available' if self.db_session else 'None'}")

    def _extract_database_metadata(
        self, patient_id: Optional[str], visit_id: Optional[int]
    ) -> Dict[str, Any]:
        """Extract comprehensive metadata from database with enhanced error handling."""
        metadata = {}

        # Validate database connection first
        if not self._validate_database_connection():
            return metadata

        exported_data_types = []

        # Extract Patient data
        try:
            patient = (
                self.db_session.query(Patient).filter(Patient.patient_id == patient_id).first()
            )

            if patient:
                metadata.update(
                    {
                        "patient_id": patient.patient_id,
                        "patient_height": patient.height_cm,
                        "patient_year_first_symptoms": patient.year_first_symptoms,
                    }
                )
                exported_data_types.append("Patient data")

        except Exception as e:
            print(f"Error extracting patient data: {e}")

        # Extract Visit data
        if visit_id:
            try:
                visit = self.db_session.query(Visit).filter(Visit.visit_id == visit_id).first()

                if visit:
                    metadata.update(
                        {
                            "visit_id": visit.visit_id,
                            "visit_year": visit.year_of_visit,
                            "visit_type": visit.visit_type,
                            "visit_therapy_type": visit.therapy_type,
                        }
                    )
                    exported_data_types.append("Visit data")

            except Exception as e:
                print(f"Error extracting visit data: {e}")

            # Extract Manometry data
            try:
                manometry = (
                    self.db_session.query(Manometry).filter(Manometry.visit_id == visit_id).first()
                )

                if manometry:
                    metadata.update(
                        {
                            "manometry_catheter_type": manometry.catheter_type,
                            "manometry_patient_position_angle": int(manometry.patient_position),
                            "manometry_resting_pressure": manometry.resting_pressure,
                            "manometry_ipr4": manometry.ipr4,
                            "manometry_dci": manometry.dci,
                            "manometry_dl": manometry.dl,
                        }
                    )
                    exported_data_types.append("Manometry data")

            except Exception as e:
                print(f"Error extracting manometry data: {e}")

            # Extract TBE (Barium Swallow) contrast information
            try:
                tbe = (
                    self.db_session.query(BariumSwallow)
                    .filter(BariumSwallow.visit_id == visit_id)
                    .first()
                )
                if tbe:
                    metadata.update(
                        {
                            "tbe_contrast_medium_type": tbe.type_contrast_medium,
                            "tbe_contrast_medium_amount_ml": tbe.amount_contrast_medium,
                        }
                    )
                    exported_data_types.append("Barium Swallow data")
            except Exception as e:
                print(f"Error extracting Barium Swallow data: {e}")

            # Extract EGD (Endoscopy) image positions if available
            try:
                from logic.services.endoscopy_service import EndoscopyFileService as _EgdFileService

                egd_service = _EgdFileService(self.db_session)
                egd_positions = egd_service.get_endoscopy_positions_for_visit(visit_id)
                if egd_positions:
                    metadata.update(
                        {
                            "egd_positions": [int(p) for p in egd_positions],
                            "egd_images_count": int(len(egd_positions)),
                        }
                    )
                    exported_data_types.append("Endoscopy image positions")
            except Exception as e:
                print(f"Error extracting EGD positions: {e}")

            # Build visit history for the patient (therapy/follow-up only)
            try:
                if "patient_id" in metadata:
                    vs = VisitService(self.db_session)
                    visits = vs.get_visits_for_patient(metadata["patient_id"]) or []
                    history = []
                    for v in visits:
                        v_type = v.get("visit_type")
                        v_year = v.get("year_of_visit") or v.get("year") or v.get("visit_year")
                        if isinstance(v_year, dict):
                            v_year = v_year.get("year")
                        # Keep only therapy or follow-up
                        if v_type and (
                            "Therapy" in v_type or "Follow-Up" in v_type or "Follow" in v_type
                        ):
                            try:
                                history.append({"visit_type": v_type, "visit_year": int(v_year)})
                            except Exception:
                                pass
                    if history:
                        # Sort chronologically
                        history = sorted(history, key=lambda x: x["visit_year"])
                        metadata["visit_history"] = history
            except Exception as e:
                print(f"Error building visit history: {e}")

            # Extract previous therapies (type and year) for the patient
            try:
                if "patient_id" in metadata:
                    from logic.services.previous_therapy_service import (
                        PreviousTherapyService as _PrevTherapyService,
                    )

                    pt_service = _PrevTherapyService(self.db_session)
                    prev_therapies = (
                        pt_service.get_prev_therapies_for_patient(metadata["patient_id"]) or []
                    )
                    pt_history = []
                    for t in prev_therapies:
                        t_type = t.get("therapy")
                        t_year = t.get("year")
                        if t_type:
                            try:
                                t_year_int = int(t_year) if t_year is not None else None
                            except Exception:
                                t_year_int = None
                            pt_history.append({"therapy_type": t_type, "therapy_year": t_year_int})
                    if pt_history:
                        # Sort chronologically (None years last)
                        pt_history = sorted(
                            pt_history,
                            key=lambda x: (
                                x["therapy_year"] is None,
                                x["therapy_year"] if x["therapy_year"] is not None else 10**9,
                            ),
                        )
                        metadata["patient_previous_therapies"] = pt_history
            except Exception as e:
                print(f"Error extracting previous therapies: {e}")

        else:
            pass

        return metadata

    def _export_single_reconstruction(
        self,
        visualization_data: VisualizationData,
        file_path: str,
        base_metadata: Dict[str, Any],
        visit_name: str,
        reconstruction_index: int,
    ) -> bool:
        """
        Export a single 3D reconstruction to VTKHDF with comprehensive attributes.
        """
        try:
            # Extract 3D mesh data
            figure_x = visualization_data.figure_x
            figure_y = visualization_data.figure_y
            figure_z = visualization_data.figure_z

            if figure_x is None or figure_y is None or figure_z is None:
                print("No 3D mesh data available")
                return False

            # Create structured mesh
            surface = self._create_mesh_from_coords(figure_x, figure_y, figure_z)
            if surface is None:
                return False

            # Add comprehensive vertex attributes
            self._add_pressure_attributes(surface, visualization_data)
            self._add_wall_thickness_attributes(surface, visualization_data)
            self._add_anatomical_region_attributes(surface, visualization_data)
            surface = self._add_geometric_attributes(surface, visualization_data)

            # Prepare comprehensive metadata
            metadata = self._prepare_comprehensive_metadata(
                base_metadata, visualization_data, visit_name, reconstruction_index
            )

            # Add metadata to mesh field data
            try:
                # Keys that must not be written to field_data
                blacklist_keys = {"patient_id", "reconstruction_index", "visit_id", "visit_name"}

                for key, value in metadata.items():
                    if key in blacklist_keys:
                        continue
                    if isinstance(value, (int, float, str, bool)):
                        surface.field_data[key] = [value]
                    elif isinstance(value, dict):
                        sanitized_value = self._sanitize_for_json(value)
                        surface.field_data[f"{key}"] = [json.dumps(sanitized_value)]
                    elif isinstance(value, (list, tuple)) and len(value) > 0:
                        # Prefer numeric arrays for flat numeric lists; otherwise JSON
                        try:
                            arr = np.asarray(value, dtype=float)
                        except Exception:
                            arr = None
                        if (
                            arr is not None
                            and np.issubdtype(arr.dtype, np.number)
                            and arr.ndim == 1
                        ):
                            surface.field_data[key] = arr
                        else:
                            clean_value = self._sanitize_for_json(value)
                            surface.field_data[f"{key}"] = [json.dumps(clean_value)]
            except Exception as e:
                print(f"Warning: Could not add metadata to mesh: {e}")

            # Ensure triangular faces
            surface = surface.triangulate()

            # Clean the mesh
            surface = surface.clean(tolerance=1e-6)

            # Compute normals for better ML features
            surface = surface.compute_normals(point_normals=True, cell_normals=True)

            # Export to VTKHDF
            return self._export_to_vtkhdf(surface, file_path)

        except Exception as e:
            print(f"Error in single reconstruction export: {e}")
            return False

    def _create_mesh_from_coords(
        self, figure_x: np.ndarray, figure_y: np.ndarray, figure_z: np.ndarray
    ) -> Optional[pv.PolyData]:
        """Create a mesh from figure data."""
        try:
            # Create structured grid preserving topology
            grid = pv.StructuredGrid(figure_x, figure_y, figure_z)

            # Extract surface while preserving structure
            surface = grid.extract_surface()

            # Clean the mesh
            surface = surface.clean(tolerance=1e-6)

            return surface

        except Exception as e:
            print(f"Error creating mesh: {e}")
            return None

    def _add_pressure_attributes(self, surface: pv.PolyData, visualization_data: VisualizationData):
        """Add HRM pressure to mesh: per-vertex (default) or compact per-slice."""

        # Early return if no pressure data requested
        if self.max_pressure_frames == 0 or self.pressure_export_mode == "none":
            return

        try:
            n_vertices = surface.n_points

            # Get pressure data from figure creator
            if hasattr(visualization_data, "figure_creator") and hasattr(
                visualization_data.figure_creator, "get_surfacecolor_list"
            ):
                surfacecolor_list = visualization_data.figure_creator.get_surfacecolor_list()
            else:
                surfacecolor_list = None

            if surfacecolor_list is not None and len(surfacecolor_list) > 0:
                n_frames = len(surfacecolor_list)

                if self.pressure_export_mode == "per_vertex":
                    # Full per-vertex mapping
                    pressure_per_frame = self._map_pressure_to_vertices(
                        surfacecolor_list, n_vertices, visualization_data
                    )
                    max_frames = (
                        n_frames
                        if self.max_pressure_frames == -1
                        else min(n_frames, self.max_pressure_frames)
                    )
                    for frame_idx in range(max_frames):
                        surface[f"pressure_frame_{frame_idx:03d}"] = pressure_per_frame[frame_idx]

                    # Also export compact per-slice HRM data alongside per-vertex (numeric only)
                    try:
                        num_slices = len(surfacecolor_list[0])
                        # Count values can be derived from shape; do not store redundant counts
                        slice_matrix = np.array(
                            surfacecolor_list[:max_frames], dtype=float
                        )  # shape (frames, slices)
                        # Numeric flattened array + shape for efficient parsing
                        surface.field_data["pressure_slice_matrix_flat"] = slice_matrix.astype(
                            np.float32
                        ).ravel(order="C")
                        surface.field_data["pressure_slice_matrix_shape"] = [
                            int(max_frames),
                            int(num_slices),
                        ]
                    except Exception as e:
                        print(f"Error exporting per-slice matrix in per-vertex mode: {e}")

                elif self.pressure_export_mode == "per_slice":
                    # Compact: keep per-slice pressures only, no per-vertex arrays (numeric only)
                    max_frames = (
                        n_frames
                        if self.max_pressure_frames == -1
                        else min(n_frames, self.max_pressure_frames)
                    )
                    # Use indices to indicate slice positions (0..num_slices-1)
                    num_slices = len(surfacecolor_list[0])

                    # Per-frame per-slice matrix and aggregate stats
                    slice_matrix = np.array(
                        surfacecolor_list[:max_frames], dtype=float
                    )  # shape (frames, slices)
                    surface.field_data["pressure_slice_matrix_flat"] = slice_matrix.astype(
                        np.float32
                    ).ravel(order="C")
                    surface.field_data["pressure_slice_matrix_shape"] = [
                        int(max_frames),
                        int(num_slices),
                    ]

        except Exception as e:
            print(f"Error adding pressure attributes: {e}")

    def _map_pressure_to_vertices(
        self,
        surfacecolor_list: List[List[float]],
        n_vertices: int,
        visualization_data: VisualizationData,
    ) -> np.ndarray:
        """Map pressure data from esophagus path to mesh vertices."""
        n_frames = len(surfacecolor_list)
        pressure_per_frame = np.zeros((n_frames, n_vertices))

        try:
            for frame_idx in range(n_frames):
                pressure_values = np.array(surfacecolor_list[frame_idx])

                if len(pressure_values) == n_vertices:
                    pressure_per_frame[frame_idx] = pressure_values
                elif len(pressure_values) > 0:
                    # Interpolate to match vertex count
                    pressure_per_frame[frame_idx] = np.interp(
                        np.linspace(0, 1, n_vertices),
                        np.linspace(0, 1, len(pressure_values)),
                        pressure_values,
                    )

        except Exception as e:
            print(f"Error in pressure mapping: {e}")

        return pressure_per_frame

    def _add_wall_thickness_attributes(
        self, surface: pv.PolyData, visualization_data: VisualizationData
    ):
        """Add wall thickness estimates per vertex, simplified to a uniform value."""
        # Use uniform wall thickness of 0.01cm for simplification, this is a placeholder for now
        wall_thickness = np.full(surface.n_points, 0.001)
        surface["wall_thickness"] = wall_thickness

    def _add_anatomical_region_attributes(
        self, surface: pv.PolyData, visualization_data: VisualizationData
    ):
        """Add anatomical region classification per vertex."""
        try:
            regions = self._classify_anatomical_regions(surface, visualization_data)

            # Add region classifications (tubular=1 and sphincter=2)
            surface["anatomical_region"] = regions

        except Exception as e:
            print(f"Error adding anatomical regions: {e}")

    def _classify_anatomical_regions(
        self, surface: pv.PolyData, visualization_data: VisualizationData
    ) -> np.ndarray:
        """
        Classify vertices into anatomical regions using axial (Z) boundaries.

        Only creates TWO regions:
        - 1: Tubular esophagus
        - 2: Lower esophageal sphincter (LES)

        Implementation details:
        - Uses the same boundary logic as the original reconstruction metrics by computing the
          sphincter start/end indices along the center path, and classifies vertices by nearest
          3D centerline index (no axial or heuristic fallbacks).
        """
        n_vertices = surface.n_points
        regions = np.ones(n_vertices, dtype=int)  # default tubular

        try:
            # Prefer Z-axis as the axial direction (right_handed_z_up)
            z_coords_vertices = surface.points[:, 2]

            # Try to derive precise sphincter Z-bounds from center-path indices
            calculated_metrics, surfacecolor_list, center_path = (
                self._invoke_figure_creator_metrics(visualization_data)
            )
            boundary_indices = self._calculate_boundary_indices(
                visualization_data, surfacecolor_list, center_path
            )

            # 1) Prepare centerline in mesh (x,y,z) using existing transform
            center_3d = self._transform_center_path_to_mesh_coordinates(
                center_path,
                visualization_data.figure_x,
                visualization_data.figure_y,
                visualization_data.figure_z,
                visualization_data,
            )

            import numpy as _np
            from scipy.spatial import cKDTree

            center_3d_arr = _np.asarray(center_3d, dtype=float)
            n_slices = center_3d_arr.shape[0]

            # Clamp boundaries
            s_start = int(
                max(0, min(n_slices - 1, int(boundary_indices.get("sphincter_start", 0))))
            )
            s_end_raw = int(boundary_indices.get("sphincter_end", n_slices - 1))
            s_end = int(max(0, min(n_slices - 1, s_end_raw + 1)))  # include the bottom-most ring
            s_lo, s_hi = (s_start, s_end) if s_start <= s_end else (s_end, s_start)

            # 2) KDTree in 3D between vertices and centerline points
            tree = cKDTree(center_3d_arr)
            _, nearest_idx = tree.query(surface.points, k=1)

            sphincter_mask = (nearest_idx >= s_lo) & (nearest_idx <= s_hi)
            regions[sphincter_mask] = 2

        except Exception as e:
            print(f"Error in region classification: {e}")

        return regions.astype(int)

    def _add_geometric_attributes(
        self, surface: pv.PolyData, visualization_data: VisualizationData
    ) -> pv.PolyData:
        """Add geometric attributes for enhanced ML features."""
        try:
            # Calculate vertex normals
            surface = surface.compute_normals(point_normals=True, cell_normals=False)

            # Add curvature information
            curvature_result = surface.curvature()
            if isinstance(curvature_result, pv.PolyData):
                surface = curvature_result
            elif isinstance(curvature_result, np.ndarray):
                surface["mean_curvature"] = curvature_result

        except Exception as e:
            print(f"Warning: Could not compute geometric attributes: {e}")

        return surface

    def _prepare_comprehensive_metadata(
        self,
        base_metadata: Dict[str, Any],
        visualization_data: VisualizationData,
        visit_name: str,
        reconstruction_index: int,
    ) -> Dict[str, Any]:
        """Prepare comprehensive metadata for the VTKHDF file."""
        metadata = base_metadata.copy()

        # Add reconstruction-specific metadata
        metadata.update(
            {
                "visit_name": visit_name,
                "reconstruction_index": reconstruction_index,
                "tbe_timepoint": int(visualization_data.xray_minute),
                "export_timestamp": datetime.now().isoformat(),
                "exporter_version": "2.0_vtkhdf",
                "coordinate_system": "right_handed_z_up",
                "file_format": "VTKHDF",
                "units": {
                    "length": "centimeters",
                    "height": "centimeters",
                    "egd_position": "centimeters",
                    "wall_thickness": "centimeters",
                    "tbe_timepoint": "minutes",
                    "pressure": "mmHg",
                    "dci": "mmH/s/cm",
                    "angle": "degrees",
                    "volume": "cm^3",
                },
            }
        )

        # Add esophagus measurements
        try:
            # Use the original calculate_metrics function from reconstruction software
            (calculated_metrics, surfacecolor_list, center_path) = (
                self._invoke_figure_creator_metrics(visualization_data)
            )
            if calculated_metrics:
                self._process_and_store_metrics(calculated_metrics, metadata, visualization_data)

            metadata["manometry_pressure_frame_rate"] = config.csv_values_per_second
            metadata["manometry_sensor_configuration"] = config.coords_sensors.copy()

        except Exception as e:
            print(f"Error preparing metadata: {e}")

        # Could be implemented even more detailed
        attribute_description = {
            "wall_thickness": "Estimated wall thickness in centimeters",
            "anatomical_region": "1=tubular, 2=LES",
            "pressure_export_mode": "none | per_slice | per_vertex",
            "tbe_contrast_medium_type": "Type of contrast medium used in TBE",
            "tbe_contrast_medium_amount_ml": "Amount of contrast medium in milliliters",
            "patient_height": "Patient height in centimeters",
            "patient_previous_therapies": "JSON serialized list of objects {therapy_type, therapy_year}",
            "visit_history": "JSON serialized list of objects {visit_type, visit_year}",
            "pressure_slice_matrix_flat": "Per-frame per-slice pressure values flattened (float32), see pressure_slice_matrix_shape",
            "pressure_slice_matrix_shape": "Two integers: [frames, slices] for reshaping pressure_slice_matrix_flat",
        }

        if (
            getattr(self, "pressure_export_mode", "per_vertex") == "per_vertex"
            and self.max_pressure_frames != 0
        ):
            attribute_description.update(
                {"pressure_frame_XXX": "HRM pressure at frame XXX in mmHg"}
            )
        elif getattr(self, "pressure_export_mode", "per_vertex") == "per_slice":
            # Counts can be derived from pressure_slice_matrix_shape; no extra description necessary
            pass

        # Add EGD descriptions only if present in metadata
        if "egd_positions" in metadata or "egd_images_count" in metadata:
            attribute_description.update(
                {
                    "egd_positions": "Positions (in cm) of EGD images along the esophagus",
                    "egd_images_count": "Number of EGD images provided",
                }
            )

        metadata.update({"ground_truth": True, "attribute_description": attribute_description})

        # Record selected pressure export mode
        metadata["pressure_export_mode"] = getattr(self, "pressure_export_mode", "per_vertex")
        return metadata

    def _invoke_figure_creator_metrics(
        self, visualization_data: "VisualizationData"
    ) -> Tuple[Optional[Dict[str, Any]], Optional[List], Optional[List]]:
        """Gather parameters and invoke the static calculate_metrics from FigureCreator."""
        try:
            # Import and instantiate the same FigureCreator as the visualization flow
            from logic.figure_creator.figure_creator_with_endoscopy import (
                FigureCreatorWithEndoscopy,
            )
            from logic.figure_creator.figure_creator_without_endoscopy import (
                FigureCreatorWithoutEndoscopy,
            )

            if getattr(visualization_data, "endoscopy_polygons", None):
                fc = FigureCreatorWithEndoscopy(visualization_data)
            else:
                fc = FigureCreatorWithoutEndoscopy(visualization_data)

            # Use exactly the same outputs as visualization for metrics and inputs
            calculated_metrics = fc.get_metrics()
            surfacecolor_list = fc.get_surfacecolor_list()
            center_path = fc.get_center_path()
            return calculated_metrics, surfacecolor_list, center_path

        except Exception as e:
            print(f"Error invoking FigureCreator.calculate_metrics: {e}")
            return None, None, None

    def _process_and_store_metrics(
        self,
        calculated_metrics: Dict[str, Any],
        metadata: Dict[str, Any],
        visualization_data: "VisualizationData",
    ):
        """Process the metrics dictionary and update metadata and visualization data."""
        # Extract metrics directly from the returned dictionary
        volume_tubular = float(calculated_metrics.get("volume_sum_tubular", 0))
        volume_sphincter = float(calculated_metrics.get("volume_sum_sphincter", 0))
        length_tubular = float(calculated_metrics.get("len_tubular", 0))
        length_sphincter = float(calculated_metrics.get("len_sphincter", 0))
        height_tubular = float(calculated_metrics.get("height_tubular_cm", length_tubular))
        height_sphincter = float(calculated_metrics.get("height_sphincter_cm", length_sphincter))

        # Store in metadata (ensure all values are JSON serializable)
        metadata.update(
            {
                "metric_volume_tubular": float(volume_tubular),
                "metric_volume_sphincter": float(volume_sphincter),
                "metric_length_tubular": float(length_tubular),
                "metric_length_sphincter": float(length_sphincter),
                "metric_height_tubular": float(height_tubular),
                "metric_height_sphincter": float(height_sphincter),
            }
        )

        # Prefer software-derived DCI (esophageal_pressurization_index) to DB value
        if "esophageal_pressurization_index" in calculated_metrics:
            val = calculated_metrics["esophageal_pressurization_index"]
            try:
                metadata["manometry_dci"] = (
                    float(val) if isinstance(val, (np.number, int, float)) else val
                )
            except Exception:
                metadata["manometry_dci"] = val

        # Store in visualization data for consistency
        visualization_data.tubular_length_cm = length_tubular
        visualization_data.sphincter_length_cm = length_sphincter

        # Also store the per-frame metrics for comprehensive export (convert numpy arrays to lists)
        if "pressure_tubular_per_frame" in calculated_metrics:
            pressure_tubular = calculated_metrics["pressure_tubular_per_frame"]
            if isinstance(pressure_tubular, np.ndarray):
                metadata["metric_pressure_tubular_per_frame"] = pressure_tubular.tolist()
            else:
                metadata["metric_pressure_tubular_per_frame"] = pressure_tubular
        if "pressure_sphincter_per_frame" in calculated_metrics:
            pressure_sphincter = calculated_metrics["pressure_sphincter_per_frame"]
            if isinstance(pressure_sphincter, np.ndarray):
                metadata["metric_pressure_sphincter_per_frame"] = pressure_sphincter.tolist()
            else:
                metadata["metric_pressure_sphincter_per_frame"] = pressure_sphincter

    def _calculate_boundary_indices(
        self,
        visualization_data: "VisualizationData",
        surfacecolor_list: List[List[float]],
        center_path: List[List[float]],
    ) -> Optional[Dict[str, int]]:
        """Calculate spatial boundary indices from the original reconstruction."""
        try:
            if surfacecolor_list is not None and len(surfacecolor_list) > 0:
                pressure_len = len(surfacecolor_list[0])

                # This ensures the evaluation model uses identical spatial boundaries
                ls_upper_pos = visualization_data.sphincter_upper_pos
                ls_lower_pos = visualization_data.esophagus_exit_pos

                if (
                    ls_upper_pos is not None
                    and ls_lower_pos is not None
                    and center_path is not None
                    and len(center_path) > 0
                ):
                    # Use KDTree to find closest points (same as calculate_metrics)
                    ls_upper_pos_yx = [
                        ls_upper_pos[1],
                        ls_upper_pos[0],
                    ]  # Switch to y,x for center_path
                    ls_lower_pos_yx = [ls_lower_pos[1], ls_lower_pos[0]]

                    _, ls_index_upper = spatial.KDTree(np.array(center_path)).query(
                        np.array(ls_upper_pos_yx)
                    )
                    _, ls_index_lower = spatial.KDTree(np.array(center_path)).query(
                        np.array(ls_lower_pos_yx)
                    )

                    # Convert numpy integers to Python integers for JSON serialization
                    ls_index_upper = int(ls_index_upper)
                    ls_index_lower = int(ls_index_lower)

                    # Store exact boundary indices used by reconstruction software
                    boundary_indices = {
                        "tubular_start": 1,
                        "tubular_end": ls_index_upper,
                        "sphincter_start": ls_index_upper + 1,
                        "sphincter_end": ls_index_lower,
                        "total_length": int(pressure_len),
                        "center_path_length": len(center_path),
                    }
                    return boundary_indices

        except Exception as boundary_error:
            print(f"Warning: Could not calculate boundary indices: {boundary_error}")

        return None

    def _export_validation_attributes(
        self,
        visualization_data: VisualizationData,
        visit_name: str,
        output_directory: str,
        base_metadata: Dict[str, Any],
        format_type: str = "json",
    ) -> Optional[str]:
        """
        Export validation attributes for validation framework consumption.

        Args:
            visualization_data: VisualizationData containing reconstruction data
            visit_name: Name identifier for the visit
            output_directory: Directory to save validation attributes
            base_metadata: Base metadata from database
            format_type: Ignored (JSON is always exported)

        Returns:
            Path to created validation attributes file, or None if failed
        """
        try:
            # Create validation data structure
            validation_data = self._extract_validation_data(visualization_data, base_metadata)
            if validation_data is None:
                return None

            base_filename = f"{visit_name}_{visualization_data.xray_minute}_validation_attributes"
            file_path = os.path.join(output_directory, f"{base_filename}.json")
            return self._save_validation_json(validation_data, file_path)

        except Exception:
            return None

    def _extract_validation_data(
        self, visualization_data: VisualizationData, base_metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract validation-specific data from VisualizationData.

        Args:
            visualization_data: VisualizationData containing reconstruction data
            base_metadata: Base metadata from database

        Returns:
            Dictionary containing validation data structure
        """
        try:
            # Extract 3D mesh data
            figure_x = visualization_data.figure_x
            figure_y = visualization_data.figure_y
            figure_z = visualization_data.figure_z

            if figure_x is None or figure_y is None or figure_z is None:
                print("No 3D mesh data available for validation export")
                return None

            # Get center path
            center_path = None
            if hasattr(visualization_data.figure_creator, "get_center_path"):
                center_path = visualization_data.figure_creator.get_center_path()
            elif hasattr(visualization_data, "center_path"):
                center_path = visualization_data.center_path

            # Get computed metrics using the existing function
            calculated_metrics, surfacecolor_list, _ = self._invoke_figure_creator_metrics(
                visualization_data
            )

            # Create validation data structure
            validation_data = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "reconstruction_name": f"{base_metadata.get('visit_name', 'Unknown')}_{visualization_data.xray_minute}",
                    "coordinate_system": "right_handed_z_up",
                    "units": {
                        "length": "centimeters",
                        "pressure": "mmHg",
                        "wall_thickness": "centimeters",
                        "volume": "cubic_centimeters",
                    },
                }
            }

            # Add center path data - TRANSFORM TO MATCH MESH COORDINATES
            if center_path is not None:
                # Transform center path to match mesh coordinate system
                transformed_center_path = self._transform_center_path_to_mesh_coordinates(
                    center_path, figure_x, figure_y, figure_z, visualization_data
                )

                validation_data["center_path"] = {
                    "points": transformed_center_path,
                    "original_pixel_points": center_path,
                    "length_cm": (
                        float(
                            calculated_metrics.get("len_tubular", 0)
                            + calculated_metrics.get("len_sphincter", 0)
                        )
                        if calculated_metrics
                        else 0.0
                    ),
                    "description": "Center path transformed to mesh coordinate system",
                }

            # Add vertices data
            points = np.column_stack((figure_x.flatten(), figure_y.flatten(), figure_z.flatten()))
            validation_data["vertices"] = {
                "points": points.tolist(),
                "count": len(points),
                "description": "Original mesh vertices",
            }

            # Add original figure coordinate bounds for consistent center path transformations
            # This ensures the same pixel coordinates always map to identical world coordinates
            # regardless of export format (STL vs VTKHDF) differences
            validation_data["original_figure_bounds"] = {
                "x_min": float(np.min(figure_x)),
                "x_max": float(np.max(figure_x)),
                "y_min": float(np.min(figure_y)),
                "y_max": float(np.max(figure_y)),
                "z_min": float(np.min(figure_z)),
                "z_max": float(np.max(figure_z)),
                "description": "Original figure coordinate bounds for consistent transformations",
            }

            # Add boundary indices for anatomical regions
            boundary_indices = self._calculate_boundary_indices(
                visualization_data, surfacecolor_list, center_path
            )
            if boundary_indices:
                validation_data["anatomical_boundaries"] = boundary_indices

            # Add volume data
            if calculated_metrics:
                validation_data["volumes"] = {
                    "volume_tubular": float(calculated_metrics.get("volume_sum_tubular", 0)),
                    "volume_sphincter": float(calculated_metrics.get("volume_sum_sphincter", 0)),
                    "total_volume": float(
                        calculated_metrics.get("volume_sum_tubular", 0)
                        + calculated_metrics.get("volume_sum_sphincter", 0)
                    ),
                    "calculated_metrics": self._sanitize_for_json(calculated_metrics),
                }

            # Add validation config with default thresholds
            validation_data["validation_config"] = {
                "thresholds": {
                    "center_path_chamfer_threshold_mm": 2.0,
                    "vertex_distance_threshold_mm": 0.1,
                    "volume_error_threshold_percent": 10.0,
                }
            }

            # Add anatomical landmarks
            if (
                hasattr(visualization_data, "sphincter_upper_pos")
                and visualization_data.sphincter_upper_pos
            ):
                validation_data["anatomical_landmarks"] = {
                    "les_upper_position": list(visualization_data.sphincter_upper_pos)
                }
                if (
                    hasattr(visualization_data, "esophagus_exit_pos")
                    and visualization_data.esophagus_exit_pos
                ):
                    validation_data["anatomical_landmarks"]["les_lower_position"] = list(
                        visualization_data.esophagus_exit_pos
                    )

            return validation_data

        except Exception as e:
            print(f"Error extracting validation data: {e}")
            return None

    def _save_validation_json(
        self, validation_data: Dict[str, Any], file_path: str
    ) -> Optional[str]:
        """Save validation data as JSON file."""
        try:
            sanitized_data = self._sanitize_for_json(validation_data)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sanitized_data, f, indent=2, ensure_ascii=False)
            return file_path
        except Exception:
            return None

    def _transform_center_path_to_mesh_coordinates(
        self,
        center_path: List[List[float]],
        figure_x: np.ndarray,
        figure_y: np.ndarray,
        figure_z: np.ndarray,
        visualization_data: VisualizationData,
    ) -> List[List[float]]:
        """
        Transform center path coordinates to match the mesh coordinate system.

        This applies the same coordinate transformations that were applied to the mesh
        during figure creation to ensure spatial alignment.

        Args:
            center_path: Original center path in pixel coordinates [(y,x), ...]
            figure_x, figure_y, figure_z: Transformed mesh coordinates
            visualization_data: VisualizationData for transformation parameters

        Returns:
            Transformed center path in mesh coordinate system [(x,y,z), ...]
        """
        try:
            if center_path is None or len(center_path) == 0:
                return []

            # Compute scale
            sensor_path = visualization_data.sensor_path
            esophagus_full_length_px = self._calculate_esophagus_length_px(
                sensor_path, visualization_data.esophagus_exit_pos
            )
            esophagus_full_length_cm = self._calculate_esophagus_full_length_cm(
                sensor_path, esophagus_full_length_px, visualization_data
            )
            px_to_cm_factor = esophagus_full_length_cm / esophagus_full_length_px

            # Map center_path (pixel) to mesh coordinate axes (robust for lists/ndarrays)
            cp = np.asarray(center_path)
            transformed_points = np.column_stack(
                (cp[:, 1], np.zeros(cp.shape[0]), cp[:, 0])
            ).astype(float)

            # Mesh bounds and centers
            mesh_x_min, mesh_x_max = float(figure_x.min()), float(figure_x.max())
            mesh_y_min, mesh_y_max = float(figure_y.min()), float(figure_y.max())
            mesh_z_min, mesh_z_max = float(figure_z.min()), float(figure_z.max())
            mesh_x_center = (mesh_x_min + mesh_x_max) / 2.0
            mesh_z_center = (mesh_z_min + mesh_z_max) / 2.0

            # Pixel mins for figure-creator style normalization
            pixel_x = transformed_points[:, 0]
            pixel_z = transformed_points[:, 2]
            pixel_x_min, pixel_y_min = float(pixel_x.min()), float(pixel_z.min())

            # Scale using px->cm factor
            scaled_x = (pixel_x - pixel_x_min) * px_to_cm_factor
            scaled_z = (pixel_z - pixel_y_min) * px_to_cm_factor

            # Center-align with mesh
            path_x_center = (scaled_x.min() + scaled_x.max()) / 2.0
            path_z_center = (scaled_z.min() + scaled_z.max()) / 2.0
            x_offset = mesh_x_center - path_x_center
            z_offset = mesh_z_center - path_z_center

            final_x = scaled_x + x_offset
            final_y = np.full_like(final_x, (mesh_y_min + mesh_y_max) / 2.0)
            final_z = scaled_z + z_offset

            return np.column_stack((final_x, final_y, final_z)).tolist()

        except Exception:
            return []

    def _calculate_esophagus_length_px(self, sensor_path, esophagus_exit_pos):
        """Calculate esophagus length in pixels (helper method)."""
        path_length_px = 0
        for i in range(1, len(sensor_path)):
            path_length_px += np.sqrt(
                (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2
                + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2
            )
            if (
                sensor_path[i][1] == esophagus_exit_pos[1]
                and sensor_path[i][0] == esophagus_exit_pos[0]
            ):
                break
        return path_length_px

    def _calculate_esophagus_full_length_cm(
        self, sensor_path, esophagus_full_length_px, visualization_data
    ):
        """Calculate esophagus length in cm (helper method)."""
        from scipy import spatial

        # Map sensor indices to centimeter
        first_sensor_cm = config.coords_sensors[visualization_data.first_sensor_index]
        second_sensor_cm = config.coords_sensors[visualization_data.second_sensor_index]

        # sensor_pos are coordinates (x, y) and sensor_path is a list of coordinates (y, x)
        first_sensor_pos_switched = (
            visualization_data.first_sensor_pos[1],
            visualization_data.first_sensor_pos[0],
        )
        second_sensor_pos_switched = (
            visualization_data.second_sensor_pos[1],
            visualization_data.second_sensor_pos[0],
        )

        # KDTree to find nearest points on the sensor_path
        _, index_first = spatial.KDTree(np.array(sensor_path)).query(
            np.array(first_sensor_pos_switched)
        )
        _, index_second = spatial.KDTree(np.array(sensor_path)).query(
            np.array(second_sensor_pos_switched)
        )

        path_length_px = 0
        for i in range(index_second, index_first + 1):
            if i > index_second:
                path_length_px += np.sqrt(
                    (sensor_path[i][0] - sensor_path[i - 1][0]) ** 2
                    + (sensor_path[i][1] - sensor_path[i - 1][1]) ** 2
                )

        length_cm = first_sensor_cm - second_sensor_cm
        return length_cm * (esophagus_full_length_px / path_length_px)

    def _export_to_vtkhdf(self, surface: pv.PolyData, file_path: str) -> bool:
        """Export the mesh with all attributes to VTKHDF format with compression."""
        try:
            import vtk

            if not hasattr(vtk, "vtkHDFWriter"):
                print("Error: vtkHDFWriter not found. Your VTK version may be too old.")
                return False

            writer = vtk.vtkHDFWriter()
            writer.SetFileName(file_path)
            writer.SetInputData(surface)

            # Set compression - check for modern and legacy methods
            if hasattr(writer, "SetUseDeflateCompression"):
                writer.SetUseDeflateCompression(True)
            elif hasattr(writer, "SetCompressionLevel"):
                writer.SetCompressionLevel(5)  # A good default compression level

            writer.Write()

            # Verify file creation and integrity
            if not os.path.exists(file_path):
                print(f"Failed to create VTKHDF file: {file_path}")
                return False

            pv.read(file_path)
            return True

        except Exception as e:
            print(f"Error during VTKHDF export or verification: {e}")
            return False


def export_single_visit_vtkhdf(
    visit_id: int,
    output_directory: str,
    db_session: Session,
    visit_name_override: Optional[str] = None,
    max_pressure_frames: int = -1,
) -> List[str]:
    """
    Export a single visit's reconstructions to VTKHDF format.

    Args:
        visit_id: Visit ID to export
        output_directory: Directory to save files
        db_session: Database session
        visit_name_override: Optional custom visit name
        max_pressure_frames: Maximum pressure frames to export (-1 for all)

    Returns:
        List of created file paths
    """
    try:
        # Initialize services
        reconstruction_service = ReconstructionService(db_session)
        patient_service = PatientService(db_session)
        visit_service = VisitService(db_session)
        barium_service = BariumSwallowFileService(db_session)
        manometry_service = ManometryFileService(db_session)
        endoscopy_service = EndoscopyFileService(db_session)
        endoflip_service = EndoflipFileService(db_session)

        # Get reconstruction for this visit
        reconstruction = reconstruction_service.get_reconstruction_for_visit(visit_id)
        if not reconstruction:
            print(f"No reconstruction found for visit {visit_id}")
            return []

        # Get visit and patient data
        visit = visit_service.get_visit(visit_id)
        patient = patient_service.get_patient(visit.patient_id)

        # Reconstruct visit data
        visit_data = _reconstruct_visit_data_from_db(
            reconstruction,
            visit,
            barium_service,
            manometry_service,
            endoscopy_service,
            endoflip_service,
        )

        if visit_data is None:
            return []

        # Create visit name
        if visit_name_override:
            visit_name = visit_name_override
        else:
            visit_name = (
                f"Visit_{visit.visit_id}_{patient.patient_id}_"
                f"{visit.visit_type.replace(' ', '')}_{visit.year_of_visit}"
            )

        # Export using enhanced exporter
        exporter = VTKHDFExporter(db_session, max_pressure_frames)
        export_result = exporter.export_visit_reconstructions(
            visit_data,
            visit_name,
            output_directory,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id,
        )

        # Extract mesh files for backward compatibility
        created_files = export_result.get("mesh_files", [])
        return created_files

    except Exception as e:
        print(f"Error exporting visit {visit_id}: {e}")
        return []


def _reconstruct_visit_data_from_db(
    reconstruction,
    visit,
    barium_service: BariumSwallowFileService,
    manometry_service: ManometryFileService,
    endoscopy_service: EndoscopyFileService,
    endoflip_service: EndoflipFileService,
) -> Optional[VisitData]:
    """
    Reconstruct VisitData from database entries.
    """
    try:
        # Handle both dictionary and object formats for reconstruction
        if isinstance(reconstruction, dict):
            reconstruction_file = reconstruction.get("reconstruction_file")
        else:
            reconstruction_file = reconstruction.reconstruction_file

        if reconstruction_file is None:
            print(f"Warning: No reconstruction file found")
            return None

        # Load the reconstructed visit data from pickle
        visit_data = pickle.loads(reconstruction_file)

        # Verify it's a VisitData object
        if not isinstance(visit_data, VisitData):
            visit_id = visit.visit_id if hasattr(visit, "visit_id") else "Unknown"
            print(f"Warning: Reconstruction for visit {visit_id} is not VisitData type")
            return None

        # Enhance with additional database information if needed
        _enhance_visit_data_with_db_info(
            visit_data,
            visit,
            barium_service,
            manometry_service,
            endoscopy_service,
            endoflip_service,
        )

        return visit_data

    except Exception as e:
        visit_id = visit.visit_id if hasattr(visit, "visit_id") else "Unknown"
        print(f"Error reconstructing visit data for visit {visit_id}: {e}")
        return None


def _enhance_visit_data_with_db_info(
    visit_data: VisitData,
    visit,
    barium_service: BariumSwallowFileService,
    manometry_service: ManometryFileService,
    endoscopy_service: EndoscopyFileService,
    endoflip_service: EndoflipFileService,
):
    """
    Enhance visit data with additional information from database.
    """
    try:
        # Get fresh data from database
        barium_files = barium_service.get_barium_swallow_files_for_visit(visit.visit_id)
        manometry_file = manometry_service.get_manometry_file_for_visit(visit.visit_id)
        endoscopy_files = endoscopy_service.get_endoscopy_files_for_visit(visit.visit_id)
        endoflip_files = endoflip_service.get_endoflip_files_for_visit(visit.visit_id)

        # Ensure each visualization has complete data
        for i, viz_data in enumerate(visit_data.visualization_data_list):
            # Ensure pressure matrix is available
            if not hasattr(viz_data, "pressure_matrix") or viz_data.pressure_matrix is None:
                if manometry_file:
                    viz_data.pressure_matrix = pickle.loads(manometry_file.pressure_matrix)

            # Ensure X-ray data is available
            if not hasattr(viz_data, "xray_file") or viz_data.xray_file is None:
                for barium_file in barium_files:
                    if barium_file.minute_of_picture == viz_data.xray_minute:
                        viz_data.xray_file = BytesIO(barium_file.file)
                        break

            # Ensure endoscopy data is available
            if endoscopy_files and (
                not hasattr(viz_data, "endoscopy_files") or not viz_data.endoscopy_files
            ):
                endoscopy_image_positions_cm = []
                endoscopy_images = []
                for endoscopy_file in endoscopy_files:
                    endoscopy_image_positions_cm.append(endoscopy_file.image_position)
                    endoscopy_images.append(BytesIO(endoscopy_file.file))

                viz_data.endoscopy_image_positions_cm = endoscopy_image_positions_cm
                viz_data.endoscopy_files = endoscopy_images

            # Ensure endoflip data is available
            if endoflip_files and (
                not hasattr(viz_data, "endoflip_screenshot") or not viz_data.endoflip_screenshot
            ):
                viz_data.endoflip_screenshot = pickle.loads(endoflip_files[0].screenshot)

    except Exception as e:
        print(f"Warning: Could not enhance visit data with database info: {e}")


def run_mass_export_with_progress(
    db_session: Session,
    output_directory: str,
    parent_widget=None,
    max_pressure_frames: int = -1,
    pressure_export_mode: str = "per_vertex",
) -> Dict[str, any]:
    """
    Export all reconstructions with progress tracking.

    Args:
        db_session: Database session
        output_directory: Directory to save files
        parent_widget: Parent widget for progress dialog
        max_pressure_frames: Maximum pressure frames to export

    Returns:
        Dictionary with export results
    """
    from logic.services.reconstruction_service import ReconstructionService
    from logic.services.patient_service import PatientService
    from logic.services.visit_service import VisitService
    from logic.services.barium_swallow_service import BariumSwallowFileService
    from logic.services.manometry_service import ManometryFileService
    from logic.services.endoscopy_service import EndoscopyFileService
    from logic.services.endoflip_service import EndoflipFileService

    # Initialize services
    reconstruction_service = ReconstructionService(db_session)
    patient_service = PatientService(db_session)
    visit_service = VisitService(db_session)
    barium_service = BariumSwallowFileService(db_session)
    manometry_service = ManometryFileService(db_session)
    endoscopy_service = EndoscopyFileService(db_session)
    endoflip_service = EndoflipFileService(db_session)

    # Initialize one exporter for the entire run
    exporter = VTKHDFExporter(
        db_session, max_pressure_frames, pressure_export_mode=pressure_export_mode
    )

    # Get all reconstructions
    all_reconstructions = reconstruction_service.get_all_reconstructions()

    if not all_reconstructions:
        return {
            "success": False,
            "message": "No reconstructions found in database",
            "total_files": 0,
            "successful_files": 0,
            "file_paths": [],
        }

    all_created_files = []
    successful_exports = 0

    # Create progress dialog if parent widget provided
    progress_dialog = None
    if parent_widget:
        try:
            from PyQt6.QtWidgets import QProgressDialog
            from PyQt6.QtCore import Qt

            progress_dialog = QProgressDialog(
                "Exporting VTKHDF files...", "Cancel", 0, len(all_reconstructions), parent_widget
            )
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.show()
        except Exception as e:
            print(f"Could not create progress dialog: {e}")

    for idx, reconstruction in enumerate(all_reconstructions):
        try:
            # Update progress
            if progress_dialog:
                progress_dialog.setValue(idx)
                progress_dialog.setLabelText(
                    f"Exporting Patient reconstruction(s) {idx + 1}/{len(all_reconstructions)}..."
                )
                if progress_dialog.wasCanceled():
                    break

            # Get visit and patient info
            visit_id = (
                reconstruction["visit_id"]
                if isinstance(reconstruction, dict)
                else reconstruction.visit_id
            )
            visit = visit_service.get_visit(visit_id)
            patient = patient_service.get_patient(visit.patient_id)

            # Reconstruct visit data
            visit_data = _reconstruct_visit_data_from_db(
                reconstruction,
                visit,
                barium_service,
                manometry_service,
                endoscopy_service,
                endoflip_service,
            )

            if visit_data is None:
                continue

            # Create visit name
            visit_name = (
                f"Visit_{visit.visit_id}_{patient.patient_id}_"
                f"{visit.visit_type.replace(' ', '')}_{visit.year_of_visit}"
            )

            # Export using the single enhanced exporter instance
            export_result = exporter.export_visit_reconstructions(
                visit_data,
                visit_name,
                output_directory,
                patient_id=patient.patient_id,
                visit_id=visit.visit_id,
            )

            # Extract mesh files and extend the list
            mesh_files = export_result.get("mesh_files", [])
            all_created_files.extend(mesh_files)
            if mesh_files:
                successful_exports += 1

        except Exception as e:
            reconstruction_id = (
                reconstruction["reconstruction_id"]
                if isinstance(reconstruction, dict)
                else reconstruction.reconstruction_id
            )
            print(f"Error exporting reconstruction {reconstruction_id}: {e}")
            continue

    # Close progress dialog
    if progress_dialog:
        progress_dialog.setValue(len(all_reconstructions))
        progress_dialog.close()

    # Provide a more detailed summary in the return dictionary
    total_reconstructions = len(all_reconstructions)
    failed_count = total_reconstructions - successful_exports

    return {
        "success": successful_exports > 0,
        "message": f"Exported {successful_exports}/{total_reconstructions} visits.",
        "exported_count": len(all_created_files),
        "failed_count": failed_count,
        "total_files": len(all_created_files),
        "output_directory": output_directory,
        "file_paths": all_created_files,
    }
