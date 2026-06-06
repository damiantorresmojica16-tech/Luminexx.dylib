cat <<EOF > Makefile
export THEOS = /workspaces/theos
include \$(THEOS)/makefiles/common.mk

TWEAK_NAME = Luminexx
Luminexx_FILES = Tweak.x

export ARCHS = arm64
export TARGET = iphone:clang:14.0:14.0

include \$(THEOS)/makefiles/tweak.mk
EOF
