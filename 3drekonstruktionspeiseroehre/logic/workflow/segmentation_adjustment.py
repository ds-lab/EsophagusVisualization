from __future__ import annotations

import re
from io import BytesIO
from typing import Optional, List

from sqlalchemy.orm import Session

from gui.master_window import MasterWindow
from gui.xray_region_selection_window import XrayRegionSelectionWindow
from logic.database.data_declarative_models import Visit as VisitModel
from logic.services.patient_service import PatientService
from logic.services.visit_service import VisitService
from logic.services.barium_swallow_service import BariumSwallowFileService
from logic.services.manometry_service import ManometryFileService
from logic.services.endoscopy_service import EndoscopyFileService
from logic.services.endoflip_service import EndoflipFileService
from logic.services.reconstruction_service import ReconstructionService
from logic.visit_data import VisitData
from logic.patient_data import PatientData


def _build_visit_name(visit_model: VisitModel, patient_id: str) -> str:
    """Create a visit name consistent with the rest of the app."""
    visit_type = (visit_model.visit_type or "").replace(" ", "")
    return f"[Visit_ID_{visit_model.visit_id}]_{patient_id}_{visit_type}_{visit_model.year_of_visit}"


def load_visitdata_from_db(db_session: Session, visit_id: int) -> Optional[VisitData]:
    """
    Load and unpickle the VisitData for a given visit from the reconstructions table.

    Returns None if no reconstruction exists or if unpickling fails.
    """
    try:
        service = ReconstructionService(db_session)
        reconstruction = service.get_reconstruction_for_visit(visit_id)
        if not reconstruction:
            return None

        import pickle

        visit_data = pickle.loads(reconstruction.reconstruction_file)
        if isinstance(visit_data, VisitData):
            return visit_data
        return None
    except Exception:
        return None


def _create_xray_windows_with_preloaded_polygons(master_window: MasterWindow, patient_data: PatientData, visit: VisitData) -> None:
    """
    Create X-ray selection windows for each visualization and preload existing polygons if present.

    The windows are linked (next_window) and the first is shown.
    """
    xray_windows: List[XrayRegionSelectionWindow] = []

    # Ensure file-like handles are rewound (e.g., BytesIO) so PIL can read them
    for viz in visit.visualization_data_list:
        try:
            if isinstance(viz.xray_file, BytesIO):
                viz.xray_file.seek(0)
        except Exception:
            pass

    # Create windows
    for n, _viz in enumerate(visit.visualization_data_list):
        w = XrayRegionSelectionWindow(master_window, patient_data, visit, n)
        xray_windows.append(w)

    # Link windows
    for i, w in enumerate(xray_windows):
        w.next_window = xray_windows[i + 1] if i < len(xray_windows) - 1 else None

        # Preload polygon points if available
        try:
            viz = visit.visualization_data_list[i]
            if hasattr(viz, "xray_polygon") and viz.xray_polygon is not None and len(viz.xray_polygon) > 2:
                # Convert numpy array to list of tuples
                preload = [(int(p[0]), int(p[1])) for p in viz.xray_polygon.tolist()]

                # Ensure selector exists and apply vertices
                if hasattr(w, "selector") and w.selector is not None:
                    w.selector.verts = preload
                    # Sync internal storage so validation/next works naturally
                    w.polygon_points["oesophagus"] = preload
                    # Redraw for immediate feedback
                    if hasattr(w, "figure_canvas") and w.figure_canvas is not None:
                        w.figure_canvas.draw_idle()
        except Exception:
            # Non-fatal: continue without preloading if anything goes wrong
            pass

    # Show the first window
    if xray_windows:
        master_window.switch_to(xray_windows[0])


def start_xray_adjustment(master_window: MasterWindow, db_session: Session, visit_id: int, visit_data_override: Optional[VisitData] = None) -> bool:
    """
    Entry point to start the X-ray segmentation adjustment workflow for a visit.

    - Loads reconstruction (VisitData) from DB
    - Reconstructs the visit name consistently
    - Creates a fresh PatientData holder
    - Starts X-ray segmentation windows with polygons preloaded

    Returns True on success, False otherwise.
    """
    # Load visit data from DB reconstruction unless an in-memory override is provided
    visit_data = visit_data_override or load_visitdata_from_db(db_session, visit_id)
    if visit_data is None:
        return False

    # Build a consistent visit name from DB for downstream file paths and UI labels
    visit_service = VisitService(db_session)
    patient_service = PatientService(db_session)
    visit_model = visit_service.get_visit(visit_id)
    if not visit_model:
        return False
    patient = patient_service.get_patient(visit_model.patient_id)
    patient_id = getattr(patient, "patient_id", "Patient") if patient else "Patient"
    visit_name = _build_visit_name(visit_model, patient_id)

    # Attach name and prepare a minimal PatientData for the workflow
    # If an override was provided, keep its name if already set; otherwise attach name
    if not getattr(visit_data, "name", None):
        visit_data.name = visit_name

    # Ensure essential data are present (rehydrate from DB if needed)
    try:
        barium_service = BariumSwallowFileService(db_session)
        manometry_service = ManometryFileService(db_session)
        endoscopy_service = EndoscopyFileService(db_session)
        endoflip_service = EndoflipFileService(db_session)

        barium_files = barium_service.get_barium_swallow_files_for_visit(visit_id)
        manometry_file = manometry_service.get_manometry_file_for_visit(visit_id)
        endoscopy_files = endoscopy_service.get_endoscopy_files_for_visit(visit_id)
        endoflip_files = endoflip_service.get_endoflip_files_for_visit(visit_id)

        # Map minute->bytes for quick lookup
        minute_to_bytes = {}
        if barium_files:
            for bf in barium_files:
                try:
                    minute_to_bytes[int(bf.minute_of_picture)] = bf.file
                except Exception:
                    pass

        for viz in visit_data.visualization_data_list:
            # X-ray file
            if getattr(viz, "xray_file", None) is None and hasattr(viz, "xray_minute"):
                try:
                    key = int(viz.xray_minute)
                    if key in minute_to_bytes:
                        viz.xray_file = BytesIO(minute_to_bytes[key])
                except Exception:
                    pass

            # Pressure matrix
            if getattr(viz, "pressure_matrix", None) is None and manometry_file is not None:
                import pickle as _pkl

                try:
                    viz.pressure_matrix = _pkl.loads(manometry_file.pressure_matrix)
                except Exception:
                    pass

            # Endoscopy images
            if getattr(viz, "endoscopy_files", None) in (None, []) and endoscopy_files:
                try:
                    positions = []
                    files = []
                    for ef in endoscopy_files:
                        positions.append(ef.image_position)
                        files.append(BytesIO(ef.file))
                    viz.endoscopy_image_positions_cm = positions
                    viz.endoscopy_files = files
                except Exception:
                    pass

            # Endoflip screenshot
            if getattr(viz, "endoflip_screenshot", None) is None and endoflip_files:
                import pickle as _pkl

                try:
                    viz.endoflip_screenshot = _pkl.loads(endoflip_files[0].screenshot)
                except Exception:
                    pass
    except Exception:
        # Non-fatal; proceed with whatever is available
        pass

    patient_data = PatientData()
    patient_data.add_visit(visit_name, visit_data)

    # Start windows with preloaded polygons
    _create_xray_windows_with_preloaded_polygons(master_window, patient_data, visit_data)
    return True


def start_hrm_adjustment(master_window: MasterWindow, db_session: Session, visit_id: int, visit_data_override: Optional[VisitData] = None) -> bool:
    """
    Entry point to start the HRM (manometry) adjustment workflow for a visit.

    - Loads reconstruction (VisitData) from DB
    - Rehydrates dependent data (x-ray, HRM, endoscopy, endoflip) if missing
    - Opens DCI selection window where the user can adjust LES/UES and the DCI window
    """
    # Load visit data unless an in-memory override is provided
    visit_data = visit_data_override or load_visitdata_from_db(db_session, visit_id)
    if visit_data is None:
        return False

    # Build visit name and ensure auxiliary data
    visit_service = VisitService(db_session)
    patient_service = PatientService(db_session)
    visit_model = visit_service.get_visit(visit_id)
    if not visit_model:
        return False
    patient = patient_service.get_patient(visit_model.patient_id)
    patient_id = getattr(patient, "patient_id", "Patient") if patient else "Patient"
    visit_name = _build_visit_name(visit_model, patient_id)
    # Preserve pre-existing name from override; otherwise attach DB-consistent name
    if not getattr(visit_data, "name", None):
        visit_data.name = visit_name

    # Rehydrate DB-backed fields very similar to xray adjustment (idempotent)
    try:
        barium_service = BariumSwallowFileService(db_session)
        manometry_service = ManometryFileService(db_session)
        endoscopy_service = EndoscopyFileService(db_session)
        endoflip_service = EndoflipFileService(db_session)

        barium_files = barium_service.get_barium_swallow_files_for_visit(visit_id)
        manometry_file = manometry_service.get_manometry_file_for_visit(visit_id)
        endoscopy_files = endoscopy_service.get_endoscopy_files_for_visit(visit_id)
        endoflip_files = endoflip_service.get_endoflip_files_for_visit(visit_id)

        minute_to_bytes = {}
        if barium_files:
            for bf in barium_files:
                try:
                    minute_to_bytes[int(bf.minute_of_picture)] = bf.file
                except Exception:
                    pass

        for viz in visit_data.visualization_data_list:
            # X-ray file
            if getattr(viz, "xray_file", None) is None and hasattr(viz, "xray_minute"):
                try:
                    key = int(viz.xray_minute)
                    if key in minute_to_bytes:
                        viz.xray_file = BytesIO(minute_to_bytes[key])
                except Exception:
                    pass

            # Pressure matrix
            if getattr(viz, "pressure_matrix", None) is None and manometry_file is not None:
                import pickle as _pkl

                try:
                    viz.pressure_matrix = _pkl.loads(manometry_file.pressure_matrix)
                except Exception:
                    pass

            # Endoscopy images
            if getattr(viz, "endoscopy_files", None) in (None, []) and endoscopy_files:
                try:
                    positions = []
                    files = []
                    for ef in endoscopy_files:
                        positions.append(ef.image_position)
                        files.append(BytesIO(ef.file))
                    viz.endoscopy_image_positions_cm = positions
                    viz.endoscopy_files = files
                except Exception:
                    pass

            # Endoflip screenshot
            if getattr(viz, "endoflip_screenshot", None) is None and endoflip_files:
                import pickle as _pkl

                try:
                    viz.endoflip_screenshot = _pkl.loads(endoflip_files[0].screenshot)
                except Exception:
                    pass

            # Rewind any BytesIO to ensure PIL can read
            try:
                if isinstance(viz.xray_file, BytesIO):
                    viz.xray_file.seek(0)
            except Exception:
                pass
    except Exception:
        pass

    # Build a fresh patient container and open DCI selection window
    patient_data = PatientData()
    patient_data.add_visit(visit_name, visit_data)

    # Lazy import to avoid heavy GUI dependency at module import
    from gui.dci_selection_window import DCISelectionWindow

    dci_window = DCISelectionWindow(master_window, patient_data, visit_data)
    master_window.switch_to(dci_window)
    return True
