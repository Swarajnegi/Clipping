"""Production download policy for the current RTX 2060 host (no AV1 decoder)."""

# Resolution outranks container/codec preference. VP9 4K must beat H.264 1080p.
# Both landscape UHD/DCI and portrait 2160x3840 fit this bound; 8K is not requested.
PRODUCTION_FORMAT = 'bv[vcodec!^=av01][width<=4096][height<=4096]+ba/b[vcodec!^=av01][width<=4096][height<=4096]'
PRODUCTION_SORT = ['res:2160', 'lang', 'fps', 'br']


def compatible_4k_available(info: dict) -> bool:
    return any(
        f.get('vcodec') not in (None, 'none') and not f['vcodec'].startswith('av01')
        and 3840 <= max(f.get('width') or 0, f.get('height') or 0) <= 4096
        for f in info.get('formats', [])
    )


def quality_record(width: int, height: int, available: bool | None) -> dict:
    native_4k = max(width, height) >= 3840
    return {'downloaded_width': width, 'downloaded_height': height,
            'native_4k': native_4k, 'compatible_4k_available': available,
            'status': ('native_4k' if min(width, height) >= 2160 else 'native_4k_wide_aspect') if native_4k else 'lower_resolution_source',
            'note': 'Export dimensions do not establish native detail; report crop/upscaling separately.'}
