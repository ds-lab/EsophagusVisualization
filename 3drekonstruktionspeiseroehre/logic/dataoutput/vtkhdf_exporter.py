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
from logic.database.data_declarative_models import (
    Patient,
    Visit,
    Manometry,
    EckardtScore,
)
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
    - Per-vertex HRM pressure data
    - Per-vertex wall thickness
    - Per-vertex anatomical region classification (LES vs tubular)
    - HDF5 organization for efficient data access
    """

    def __init__(
        self, db_session: Optional[Session] = None, max_pressure_frames: int = -1
    ):
        """
        Initialize the VTKHDF Exporter.

        Args:
            db_session: Database session for metadata extraction
            max_pressure_frames: Maximum number of pressure frames to export (-1 for all)
        """
        self.db_session = db_session
        self.max_pressure_frames = max_pressure_frames

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
    ) -> List[str]:
        """
        Export all reconstructions from a visit to VTKHDF files.

        Args:
            visit_data: VisitData containing visualization data
            visit_name: Name identifier for the visit
            output_directory: Directory to save VTKHDF files
            patient_id: Patient ID for metadata
            visit_id: Visit ID for database metadata lookup

        Returns:
            List of created file paths
        """
        created_files = []

        # Log export parameters for debugging
        print(f"\nStarting VTKHDF export for visit: {visit_name}")
        self._log_export_parameters(patient_id, visit_id, visit_name)

        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Extract database metadata if available
        print(f"\nExtracting database metadata...")
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
                    created_files.append(file_path)
                    print(f"Successfully exported: {file_name}")
                else:
                    print(f"Failed to export: {file_name}")

            except Exception as e:
                print(f"Error exporting visualization {i}: {str(e)}")
                continue

        # Export summary
        total_visualizations = len(visit_data.visualization_data_list)
        successful_exports = len(created_files)
        failed_exports = total_visualizations - successful_exports

        print(f"\nExport Summary for visit: {visit_name}")
        print(
            f"Successfully exported: {successful_exports}/{total_visualizations} visualizations"
        )
        if failed_exports > 0:
            print(f"Failed exports: {failed_exports}")

        has_database_metadata = bool(metadata)
        print(f"Database metadata included: {'Yes' if has_database_metadata else 'No'}")

        if created_files:
            print(f"Files created in: {output_directory}")
            for file_path in created_files:
                print(f"  - {os.path.basename(file_path)}")

        return created_files

    def _validate_database_connection(self) -> bool:
        """
        Validate if database connection is active and accessible.

        Returns:
            bool: True if database connection is valid, False otherwise
        """
        if not self.db_session:
            print(
                "No database session provided - patient and clinical data will not be exported"
            )
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
        print(f"Export Parameters:")
        print(
            f"  Patient ID: {patient_id if patient_id else 'None (WARNING: No patient data will be exported)'}"
        )
        print(
            f"  Visit ID: {visit_id if visit_id else 'None (WARNING: No visit data will be exported)'}"
        )
        print(f"  Visit Name: {visit_name}")
        print(
            f"  Database Session: {'Available' if self.db_session else 'None (WARNING: No database metadata will be exported)'}"
        )

    def _extract_database_metadata(
        self, patient_id: Optional[str], visit_id: Optional[int]
    ) -> Dict[str, Any]:
        """Extract comprehensive metadata from database with enhanced error handling."""
        metadata = {}

        # Validate database connection first
        if not self._validate_database_connection():
            return metadata

        # Check patient_id
        if not patient_id:
            print("No patient ID provided - patient data will not be exported")
            return metadata

        exported_data_types = []

        # Extract Patient data
        try:
            patient = (
                self.db_session.query(Patient)
                .filter(Patient.patient_id == patient_id)
                .first()
            )

            if patient:
                metadata.update(
                    {
                        "patient_id": patient.patient_id,
                        "patient_gender": patient.gender,
                        "patient_ethnicity": patient.ethnicity,
                        "patient_birth_year": patient.birth_year,
                        "patient_year_first_diagnosis": patient.year_first_diagnosis,
                        "patient_year_first_symptoms": patient.year_first_symptoms,
                        "patient_center": patient.center,
                    }
                )
                exported_data_types.append("Patient data")
                print(
                    f"Successfully extracted patient data for patient ID: {patient_id}"
                )
            else:
                print(f"No patient found for patient ID: {patient_id}")

        except Exception as e:
            print(f"Error extracting patient data: {e}")

        # Extract Visit data
        if visit_id:
            try:
                visit = (
                    self.db_session.query(Visit)
                    .filter(Visit.visit_id == visit_id)
                    .first()
                )

                if visit:
                    metadata.update(
                        {
                            "visit_id": visit.visit_id,
                            "visit_year": visit.year_of_visit,
                            "visit_type": visit.visit_type,
                            "therapy_type": visit.therapy_type,
                            "months_after_initial_therapy": visit.months_after_initial_therapy,
                            "months_after_last_therapy": visit.months_after_last_therapy,
                            "months_after_diagnosis": visit.months_after_diagnosis,
                        }
                    )
                    exported_data_types.append("Visit data")
                    print(f"Successfully extracted visit data for visit ID: {visit_id}")
                else:
                    print(f"No visit found for visit ID: {visit_id}")

            except Exception as e:
                print(f"Error extracting visit data: {e}")

            # Extract Manometry data
            try:
                manometry = (
                    self.db_session.query(Manometry)
                    .filter(Manometry.visit_id == visit_id)
                    .first()
                )

                if manometry:
                    metadata.update(
                        {
                            "manometry_catheter_type": manometry.catheter_type,
                            "manometry_patient_position": manometry.patient_position,
                            "manometry_resting_pressure": manometry.resting_pressure,
                            "manometry_ipr4": manometry.ipr4,
                            "manometry_dci": manometry.dci,
                            "manometry_dl": manometry.dl,
                            "manometry_ues_upper": manometry.ues_upper_boundary,
                            "manometry_ues_lower": manometry.ues_lower_boundary,
                            "manometry_les_upper": manometry.les_upper_boundary,
                            "manometry_les_lower": manometry.les_lower_boundary,
                            "manometry_les_length": manometry.les_length,
                        }
                    )
                    exported_data_types.append("Manometry data")
                    print(
                        f"Successfully extracted manometry data for visit ID: {visit_id}"
                    )
                else:
                    print(f"No manometry data found for visit ID: {visit_id}")

            except Exception as e:
                print(f"Error extracting manometry data: {e}")

            # Extract Eckardt Score data
            try:
                eckardt = (
                    self.db_session.query(EckardtScore)
                    .filter(EckardtScore.visit_id == visit_id)
                    .first()
                )

                if eckardt:
                    metadata.update(
                        {
                            "eckardt_total_score": eckardt.total_score,
                            "eckardt_dysphagia": eckardt.dysphagia,
                            "eckardt_retrosternal_pain": eckardt.retrosternal_pain,
                            "eckardt_regurgitation": eckardt.regurgitation,
                            "eckardt_weightloss": eckardt.weightloss,
                        }
                    )
                    exported_data_types.append("Eckardt Score data")
                    print(
                        f"Successfully extracted Eckardt Score data for visit ID: {visit_id}"
                    )
                else:
                    print(f"No Eckardt Score data found for visit ID: {visit_id}")

            except Exception as e:
                print(f"Error extracting Eckardt Score data: {e}")
        else:
            print(
                "No visit ID provided - visit-related data (visit, manometry, Eckardt) will not be exported"
            )

        # Summary of exported database metadata
        if exported_data_types:
            print(f"Database metadata export summary: {', '.join(exported_data_types)}")
        else:
            print(
                "No database metadata was exported - files will only contain computed reconstruction data"
            )

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
                for key, value in metadata.items():
                    if isinstance(value, (int, float, str, bool)):
                        surface.field_data[key] = [value]
                    elif isinstance(value, dict):
                        sanitized_value = self._sanitize_for_json(value)
                        surface.field_data[f"{key}_json"] = [
                            json.dumps(sanitized_value)
                        ]
                    elif isinstance(value, (list, tuple)) and len(value) > 0:
                        # Handle numpy arrays in lists
                        try:
                            # Convert numpy arrays to Python lists for serialization
                            if isinstance(value, np.ndarray):
                                clean_value = value.tolist()
                            elif isinstance(value, (list, tuple)):
                                clean_value = []
                                for item in value:
                                    if isinstance(item, np.ndarray):
                                        clean_value.append(item.tolist())
                                    elif isinstance(item, (np.integer, np.floating)):
                                        clean_value.append(float(item))
                                    else:
                                        clean_value.append(item)
                            else:
                                clean_value = value
                            surface.field_data[f"{key}_json"] = [
                                json.dumps(clean_value)
                            ]
                        except Exception as json_error:
                            print(f"Warning: Could not serialize {key}: {json_error}")
                            # Skip this metadata item
                            continue
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

    def _add_pressure_attributes(
        self, surface: pv.PolyData, visualization_data: VisualizationData
    ):
        """Add comprehensive HRM pressure data as vertex attributes."""
        
        # Early return if no vertex pressure data requested
        if self.max_pressure_frames == 0:
            print("Skipping per-vertex pressure data export as requested (metadata will still be exported)")
            return
        
        try:
            n_vertices = surface.n_points

            # Get pressure data from figure creator
            if hasattr(visualization_data.figure_creator, "get_surfacecolor_list"):
                surfacecolor_list = (
                    visualization_data.figure_creator.get_surfacecolor_list()
                )

                if surfacecolor_list is not None and len(surfacecolor_list) > 0:
                    n_frames = len(surfacecolor_list)
                    n_pressure_points = len(surfacecolor_list[0])

                    # Map pressure data to mesh vertices
                    pressure_per_frame = self._map_pressure_to_vertices(
                        surfacecolor_list, n_vertices, visualization_data
                    )

                    # Add per-frame pressure data (configurable limit to avoid huge files)
                    if self.max_pressure_frames == -1:
                        max_frames = n_frames  # Export all frames
                    else:
                        max_frames = min(n_frames, self.max_pressure_frames)

                    for frame_idx in range(max_frames):
                        surface[f"pressure_frame_{frame_idx:03d}"] = pressure_per_frame[
                            frame_idx
                        ]

                    # Add pressure statistics
                    all_pressures = np.array(pressure_per_frame)
                    surface["pressure_max"] = np.max(all_pressures, axis=0)
                    surface["pressure_min"] = np.min(all_pressures, axis=0)
                    surface["pressure_mean"] = np.mean(all_pressures, axis=0)
                    surface["pressure_std"] = np.std(all_pressures, axis=0)

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
        # Use uniform wall thickness of 0.35cm for simplification
        wall_thickness = np.full(surface.n_points, 0.35)
        surface["wall_thickness_cm"] = wall_thickness

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
        Classify vertices into anatomical regions following the reconstruction software logic.

        Only creates TWO regions:
        - Region 1: Tubular esophagus
        - Region 2: Sphincter

        This matches the original calculate_metrics function in figure_creator.py
        """
        n_vertices = surface.n_points
        regions = np.ones(n_vertices, dtype=int)  # Default to tubular

        try:
            # Get boundary positions (same as in calculate_metrics)
            ls_upper_pos = visualization_data.sphincter_upper_pos  # [x, y]
            ls_lower_pos = visualization_data.esophagus_exit_pos  # [x, y]

            # Get mesh coordinate bounds
            points = surface.points
            y_coords = points[:, 1]  # Y coordinates
            y_min, y_max = np.min(y_coords), np.max(y_coords)
            mesh_y_range = y_max - y_min

            # Calculate sphincter region boundaries in mesh coordinates
            # The sphincter is typically in the lower portion of the esophagus
            if (
                ls_upper_pos[1] < ls_lower_pos[1]
            ):  # Normal case: upper pos has lower Y pixel
                # Sphincter is at the bottom of the mesh (higher Y values)
                sphincter_start_ratio = 0.75  # Start at 75% along the esophagus
                sphincter_end_ratio = 0.95  # End at 95% along the esophagus
            else:  # Inverted case
                sphincter_start_ratio = 0.05  # Start at 5% along the esophagus
                sphincter_end_ratio = 0.25  # End at 25% along the esophagus

            sphincter_y_start = y_min + (sphincter_start_ratio * mesh_y_range)
            sphincter_y_end = y_min + (sphincter_end_ratio * mesh_y_range)

            # Ensure proper ordering
            sphincter_y_min = min(sphincter_y_start, sphincter_y_end)
            sphincter_y_max = max(sphincter_y_start, sphincter_y_end)

            # Classify vertices: tubular (1) and sphincter (2)
            sphincter_mask = (y_coords >= sphincter_y_min) & (
                y_coords <= sphincter_y_max
            )
            regions[sphincter_mask] = 2  # Sphincter region

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
                "xray_minute": str(visualization_data.xray_minute),
                "export_timestamp": datetime.now().isoformat(),
                "exporter_version": "2.0_vtkhdf",
                "coordinate_system": "right_handed_y_up",
                "file_format": "VTKHDF",
                "units": {
                    "length": "centimeters",
                    "pressure": "mmHg",
                    "wall_thickness": "centimeters",
                    "time": "seconds",
                },
            }
        )

        # Add esophagus measurements
        try:
            if hasattr(
                visualization_data.figure_creator, "get_esophagus_full_length_cm"
            ):
                metadata["esophagus_length_cm"] = float(
                    visualization_data.figure_creator.get_esophagus_full_length_cm()
                )

            # Use the original calculate_metrics function from reconstruction software
            (
                calculated_metrics,
                surfacecolor_list,
                center_path,
            ) = self._invoke_figure_creator_metrics(visualization_data)
            if calculated_metrics:
                self._process_and_store_metrics(
                    calculated_metrics, metadata, visualization_data
                )

                # Store boundary information for evaluation model to use exact same spatial indices
                boundary_indices = self._calculate_boundary_indices(
                    visualization_data, surfacecolor_list, center_path
                )
                if boundary_indices:
                    metadata["boundary_indices"] = boundary_indices

            # Add acquisition parameters
            if hasattr(visualization_data.figure_creator, "get_number_of_frames"):
                metadata["n_pressure_frames"] = (
                    visualization_data.figure_creator.get_number_of_frames()
                )

            metadata["pressure_frame_rate"] = config.csv_values_per_second
            metadata["sensor_configuration"] = config.coords_sensors.copy()

            # Add anatomical landmarks
            if (
                hasattr(visualization_data, "sphincter_upper_pos")
                and visualization_data.sphincter_upper_pos
            ):
                metadata["les_upper_position"] = list(
                    visualization_data.sphincter_upper_pos
                )

            if (
                hasattr(visualization_data, "esophagus_exit_pos")
                and visualization_data.esophagus_exit_pos
            ):
                metadata["les_lower_position"] = list(
                    visualization_data.esophagus_exit_pos
                )

        except Exception as e:
            print(f"Error preparing metadata: {e}")

        # Add ML-specific metadata
        metadata.update(
            {
                "ground_truth": True,
                "attribute_description": {
                    "pressure_frame_XXX": "HRM pressure at frame XXX in mmHg",
                    "pressure_max": "Maximum pressure across all frames in mmHg",
                    "pressure_min": "Minimum pressure across all frames in mmHg",
                    "pressure_mean": "Mean pressure across all frames in mmHg",
                    "pressure_std": "Standard deviation of pressure across all frames",
                    "wall_thickness_cm": "Estimated wall thickness in centimeters",
                    "anatomical_region": "1=tubular, 2=LES",
                },
            }
        )

        return metadata

    def _invoke_figure_creator_metrics(
        self, visualization_data: "VisualizationData"
    ) -> Tuple[Optional[Dict[str, Any]], Optional[List], Optional[List]]:
        """Gather parameters and invoke the static calculate_metrics from FigureCreator."""
        try:
            # Import the original function
            from logic.figure_creator.figure_creator import FigureCreator

            # Get all required parameters for the original function
            figure_x = visualization_data.figure_x
            figure_y = visualization_data.figure_y

            # Get pressure data (surfacecolor_list)
            surfacecolor_list = None
            if hasattr(visualization_data.figure_creator, "get_surfacecolor_list"):
                surfacecolor_list = (
                    visualization_data.figure_creator.get_surfacecolor_list()
                )

            # Get center path
            center_path = None
            if hasattr(visualization_data.figure_creator, "get_center_path"):
                center_path = visualization_data.figure_creator.get_center_path()
            elif hasattr(visualization_data, "center_path"):
                center_path = visualization_data.center_path

            # Get max index
            max_index = None
            if center_path is not None:
                max_index = len(center_path) - 1

            # Get esophagus length
            esophagus_full_length_cm = None
            esophagus_full_length_px = None
            if hasattr(
                visualization_data.figure_creator, "get_esophagus_full_length_cm"
            ):
                esophagus_full_length_cm = (
                    visualization_data.figure_creator.get_esophagus_full_length_cm()
                )
            if hasattr(
                visualization_data.figure_creator, "get_esophagus_full_length_px"
            ):
                esophagus_full_length_px = (
                    visualization_data.figure_creator.get_esophagus_full_length_px()
                )

            # Calculate pixel length if not available, as it's required for metrics
            if esophagus_full_length_px is None and center_path is not None:
                esophagus_full_length_px = FigureCreator.calculate_path_length_px(
                    center_path
                )

            # Check if we have all required parameters
            params_valid = (
                figure_x is not None
                and figure_y is not None
                and surfacecolor_list is not None
                and center_path is not None
                and max_index is not None
                and esophagus_full_length_cm is not None
                and esophagus_full_length_px is not None
            )

            if not params_valid:
                print(
                    "Warning: Missing parameters for FigureCreator.calculate_metrics."
                )
                return None, None, None

            # Call the original calculate_metrics function
            calculated_metrics = FigureCreator.calculate_metrics(
                visualization_data,
                figure_x,
                figure_y,
                surfacecolor_list,
                center_path,
                max_index,
                esophagus_full_length_cm,
                esophagus_full_length_px,
            )
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
        height_tubular = float(
            calculated_metrics.get("height_tubular_cm", length_tubular)
        )
        height_sphincter = float(
            calculated_metrics.get("height_sphincter_cm", length_sphincter)
        )

        # Store in metadata (ensure all values are JSON serializable)
        metadata.update(
            {
                "volume_tubular_cm3": float(volume_tubular),
                "volume_sphincter_cm3": float(volume_sphincter),
                "length_tubular_cm": float(length_tubular),
                "length_sphincter_cm": float(length_sphincter),
                "height_tubular_cm": float(height_tubular),
                "height_sphincter_cm": float(height_sphincter),
            }
        )

        # Store additional overall metrics (convert numpy types to Python types)
        if "metric_tubular_overall" in calculated_metrics:
            val = calculated_metrics["metric_tubular_overall"]
            metadata["metric_tubular_overall"] = (
                float(val) if isinstance(val, (np.number, int, float)) else val
            )
        if "metric_sphincter_overall" in calculated_metrics:
            val = calculated_metrics["metric_sphincter_overall"]
            metadata["metric_sphincter_overall"] = (
                float(val) if isinstance(val, (np.number, int, float)) else val
            )
        if "pressure_tubular_overall" in calculated_metrics:
            val = calculated_metrics["pressure_tubular_overall"]
            metadata["pressure_tubular_overall"] = (
                float(val) if isinstance(val, (np.number, int, float)) else val
            )
        if "pressure_sphincter_overall" in calculated_metrics:
            val = calculated_metrics["pressure_sphincter_overall"]
            metadata["pressure_sphincter_overall"] = (
                float(val) if isinstance(val, (np.number, int, float)) else val
            )
        if "esophageal_pressurization_index" in calculated_metrics:
            val = calculated_metrics["esophageal_pressurization_index"]
            metadata["esophageal_pressurization_index"] = (
                float(val) if isinstance(val, (np.number, int, float)) else val
            )

        # Store in visualization data for consistency
        visualization_data.tubular_length_cm = length_tubular
        visualization_data.sphincter_length_cm = length_sphincter

        # Also store the per-frame metrics for comprehensive export (convert numpy arrays to lists)
        if "metric_tubular" in calculated_metrics:
            metric_tubular = calculated_metrics["metric_tubular"]
            if isinstance(metric_tubular, np.ndarray):
                metadata["metric_tubular_per_frame"] = metric_tubular.tolist()
            else:
                metadata["metric_tubular_per_frame"] = metric_tubular
        if "metric_sphincter" in calculated_metrics:
            metric_sphincter = calculated_metrics["metric_sphincter"]
            if isinstance(metric_sphincter, np.ndarray):
                metadata["metric_sphincter_per_frame"] = metric_sphincter.tolist()
            else:
                metadata["metric_sphincter_per_frame"] = metric_sphincter
        if "pressure_tubular_per_frame" in calculated_metrics:
            pressure_tubular = calculated_metrics["pressure_tubular_per_frame"]
            if isinstance(pressure_tubular, np.ndarray):
                metadata["pressure_tubular_per_frame"] = pressure_tubular.tolist()
            else:
                metadata["pressure_tubular_per_frame"] = pressure_tubular
        if "pressure_sphincter_per_frame" in calculated_metrics:
            pressure_sphincter = calculated_metrics["pressure_sphincter_per_frame"]
            if isinstance(pressure_sphincter, np.ndarray):
                metadata["pressure_sphincter_per_frame"] = pressure_sphincter.tolist()
            else:
                metadata["pressure_sphincter_per_frame"] = pressure_sphincter

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
        created_files = exporter.export_visit_reconstructions(
            visit_data,
            visit_name,
            output_directory,
            patient_id=patient.patient_id,
            visit_id=visit.visit_id,
        )

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
        endoscopy_files = endoscopy_service.get_endoscopy_files_for_visit(
            visit.visit_id
        )
        endoflip_files = endoflip_service.get_endoflip_files_for_visit(visit.visit_id)

        # Ensure each visualization has complete data
        for i, viz_data in enumerate(visit_data.visualization_data_list):
            # Ensure pressure matrix is available
            if (
                not hasattr(viz_data, "pressure_matrix")
                or viz_data.pressure_matrix is None
            ):
                if manometry_file:
                    viz_data.pressure_matrix = pickle.loads(
                        manometry_file.pressure_matrix
                    )

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
                not hasattr(viz_data, "endoflip_screenshot")
                or not viz_data.endoflip_screenshot
            ):
                viz_data.endoflip_screenshot = pickle.loads(
                    endoflip_files[0].screenshot
                )

    except Exception as e:
        print(f"Warning: Could not enhance visit data with database info: {e}")


def run_mass_export_with_progress(
    db_session: Session,
    output_directory: str,
    parent_widget=None,
    max_pressure_frames: int = -1,
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
    exporter = VTKHDFExporter(db_session, max_pressure_frames)

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
                "Exporting VTKHDF files...",
                "Cancel",
                0,
                len(all_reconstructions),
                parent_widget,
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
            created_files = exporter.export_visit_reconstructions(
                visit_data,
                visit_name,
                output_directory,
                patient_id=patient.patient_id,
                visit_id=visit.visit_id,
            )

            all_created_files.extend(created_files)
            if created_files:
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
