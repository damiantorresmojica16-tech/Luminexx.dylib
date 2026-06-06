# Forzar asignación inmediata con :=
SDKROOT := /workspaces/theos/sdks/iPhoneOS14.5.sdk
export SDKROOT

include $(THEOS)/makefiles/common.mk
...

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = Luminexx
Luminexx_FILES = Tweak.x

# Forzamos el target para que no intente autodetectar nada
export TARGET = iphone:clang:14.5:14.5
export ARCHS = arm64

include $(THEOS)/makefiles/tweak.mk
