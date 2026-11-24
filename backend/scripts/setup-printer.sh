#!/usr/bin/env bash
#
# Configure the DNP QW410 dye-sublimation photo printer on Linux/CUPS.
#
# The QW410 needs the Gutenprint driver (it speaks a proprietary DNP protocol),
# not the HP driver that plug-and-play may have auto-selected. This script:
#   1. installs CUPS-related deps
#   2. builds & installs Gutenprint from source (provides the gutenprint53+usb backend)
#   3. generates the DNP PPD
#   4. creates a CUPS queue "DP-QW410" with the correct backend + 4x6 page size
#   5. rewrites the 4x6 PPD page geometry to the TRUE paper size so the photo
#      prints 1:1 pixel-to-pixel (no zoom/crop, no white border)
#
# The stock Gutenprint PPD declares w288h432 (4x6) with a borderless overscan
# box: PageSize/PageRegion/PaperDimension = 337.92x440.64pt (4.69"x6.12") while
# the physical paper is 288x432pt (4"x6"). CUPS then renders a 1408x1836 raster
# and the driver rescales/crops it onto the paper -> zoomed/cropped prints.
# We rewrite all geometry lines for w288h432 to 288x432pt so the CUPS raster is
# exactly 1200x1800 at 300 dpi and maps dot-for-dot onto the paper.
#
# The script is idempotent: if Gutenprint and the queue already exist it only
# re-patches the PPD geometry and restarts CUPS (seconds, not a full rebuild).
#
# Run as root:  sudo bash setup-printer.sh
set -euo pipefail

GUTENPRINT_URL="https://downloads.sourceforge.net/project/gimp-print/gutenprint-5.3/5.3.5/gutenprint-5.3.5.tar.xz"
QUEUE="DP-QW410"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash $0" >&2
  exit 1
fi

# Rewrite every 4x6 geometry line in a PPD to the true paper size (288x432pt).
# Handles both stock (comma decimals, 337.92 overscan box) and already-patched
# (dot decimals) PPDs. Anchored to the exact option name so the -div2/-div3 and
# combined media sizes are left untouched.
patch_ppd_geometry() {
  local ppd="$1"
  [[ -f "$ppd" ]] || return 0
  sed -i -E \
    -e 's|^\*PageSize w288h288/4x4:.*|\*PageSize w288h288/4x4:\t"<</PageSize[288 288]/ImagingBBox null>>setpagedevice"|' \
    -e 's|^\*PageRegion w288h288/4x4:.*|\*PageRegion w288h288/4x4:\t"<</PageSize[288 288]/ImagingBBox null>>setpagedevice"|' \
    -e 's|^\*PaperDimension w288h288/4x4:.*|\*PaperDimension w288h288/4x4:\t"288 288"|' \
    -e 's|^\*ImageableArea w288h288/4x4:.*|\*ImageableArea w288h288/4x4:\t"0 0 288 288"|' \
    -e 's|^\*PageSize w432h288/6x4:.*|\*PageSize w432h288/6x4:\t"<</PageSize[432 288]/ImagingBBox null>>setpagedevice"|' \
    -e 's|^\*PageRegion w432h288/6x4:.*|\*PageRegion w432h288/6x4:\t"<</PageSize[432 288]/ImagingBBox null>>setpagedevice"|' \
    -e 's|^\*PaperDimension w432h288/6x4:.*|\*PaperDimension w432h288/6x4:\t"432 288"|' \
    -e 's|^\*ImageableArea w432h288/6x4:.*|\*ImageableArea w432h288/6x4:\t"0 0 432 288"|' \
    -e 's|^\*PageSize w288h432/4x6:.*|\*PageSize w288h432/4x6:\t"<</PageSize[288 432]/ImagingBBox null>>setpagedevice"|' \
    -e 's|^\*PageRegion w288h432/4x6:.*|\*PageRegion w288h432/4x6:\t"<</PageSize[288 432]/ImagingBBox null>>setpagedevice"|' \
    -e 's|^\*PaperDimension w288h432/4x6:.*|\*PaperDimension w288h432/4x6:\t"288 432"|' \
    -e 's|^\*ImageableArea w288h432/4x6:.*|\*ImageableArea w288h432/4x6:\t"0 0 288 432"|' \
    "$ppd"
  echo "    patched geometry: $ppd"
}

# ---------- Fast path: already installed -> only re-patch + restart ----------
if command -v cups-genppd.5.3 >/dev/null 2>&1 \
  && lpstat -p "${QUEUE}" >/dev/null 2>&1 \
  && [[ -f "/etc/cups/ppd/${QUEUE}.ppd" ]]; then
  echo "==> Gutenprint and queue '${QUEUE}' already installed; re-patching PPD geometry..."
  patch_ppd_geometry "/etc/cups/ppd/stp-dnp-qw410.5.3.ppd"
  patch_ppd_geometry "/etc/cups/ppd/${QUEUE}.ppd"
  echo "==> Restarting CUPS..."
  systemctl restart cups || service cups restart
  echo "==> Done. Status:"
  lpstat -p "${QUEUE}"
  echo "Printer '${QUEUE}' is ready. Test:  lp -d ${QUEUE} -o media=w288h432 <image.jpg>"
  exit 0
fi

echo "==> Detecting DNP QW410 USB device..."
SERIAL="$(lpstat -v 2>/dev/null | grep -i "nippon" | grep -oE 'serial=[A-Za-z0-9]+' | cut -d= -f2 | head -1)"
if [[ -z "$SERIAL" ]]; then
  echo "ERROR: QW410 not found. Run: lpstat -v | grep -i nippon" >&2
  exit 1
fi
URI="gutenprint53+usb://dnp-qw410/${SERIAL}"
echo "    serial=${SERIAL}  uri=${URI}"

echo "==> Installing dependencies..."
apt-get update -y
apt-get install -y --no-install-recommends \
  cups cups-client cups-bsd \
  build-essential libusb-1.0-0-dev libcups2-dev libtool autoconf pkg-config \
  || apt-get install -y build-essential libusb-1.0-0-dev libcups2-dev libtool autoconf pkg-config

echo "==> Removing ipp-usb (can hijack the USB device)..."
# shellcheck disable=SC2015
apt-get remove -y ipp-usb >/dev/null 2>&1 || true

echo "==> Building Gutenprint from source (this can take a few minutes)..."
cd /tmp
rm -rf gutenprint-src gutenprint-5.3.5.tar.xz
if ! wget -q "${GUTENPRINT_URL}" -O gutenprint-5.3.5.tar.xz; then
  echo "ERROR: could not download Gutenprint. Check network." >&2
  exit 1
fi
mkdir gutenprint-src
tar -xJf gutenprint-5.3.5.tar.xz -C gutenprint-src --strip-components=1
cd gutenprint-src
./configure --without-doc
make -j"$(nproc)"
make install
ldconfig
cd /tmp
rm -rf gutenprint-src gutenprint-5.3.5.tar.xz

echo "==> Generating the DNP QW410 PPD..."
GENPPD="$(command -v cups-genppd.5.3)"
if [[ -z "$GENPPD" ]]; then
  echo "ERROR: cups-genppd.5.3 not found after install." >&2
  exit 1
fi
mkdir -p /etc/cups/ppd
"${GENPPD}" -p /etc/cups/ppd dnp-qw410
PPD="/etc/cups/ppd/stp-dnp-qw410.5.3.ppd"
if [[ ! -f "$PPD" ]]; then
  PPD=$(ls /etc/cups/ppd/stp-dnp-qw410*.ppd 2>/dev/null | head -1)
fi
gunzip -f "${PPD}.gz" 2>/dev/null || true
LPPD="${PPD}"
echo "    PPD=${LPPD}"

echo "==> Creating queue '${QUEUE}' (4x6)..."
lpadmin -x "${QUEUE}" >/dev/null 2>&1 || true
lpadmin -p "${QUEUE}" \
  -v "${URI}" \
  -E \
  -P "${LPPD}" \
  -o PageSize=w288h432 \
  -D "DNP QW410 4x6"
lpadmin -p "${QUEUE}" -o PageSize=w288h432

echo "==> Rewriting 4x6 PPD geometry to true paper size (288x432pt, 1:1 pixels)..."
patch_ppd_geometry "${LPPD}"
patch_ppd_geometry "/etc/cups/ppd/${QUEUE}.ppd"
systemctl restart cups || service cups restart

echo "==> Done. Status:"
lpstat -p "${QUEUE}"
echo "Printer '${QUEUE}' is ready. Test:  lp -d ${QUEUE} -o media=w288h432 <image.jpg>"
