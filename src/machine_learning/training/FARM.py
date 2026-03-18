from .sumo_site_metrics import collect_site_detector_profiles, detector_output_files, parse_detector_hourly_counts


def extraer_nVeh(file_path, det):
    return parse_detector_hourly_counts(det + "/" + file_path)


def define_files(Detector_file):
    site_dir = Detector_file.rsplit("/", 1)[0]
    return detector_output_files(site_dir)


def farm(det):
    per_detector, _ = collect_site_detector_profiles(det)
    return per_detector
