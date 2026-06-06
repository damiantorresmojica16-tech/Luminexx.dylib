export THEOS = /workspaces/theos
# Definimos el SDK de forma explícita
export SDKROOT = /workspaces/theos/sdks/iPhoneOS14.5.sdk
# Forzamos la versión del SDK aquí también
export SDKVERSION = 14.5

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = Luminexx
Luminexx_FILES = Tweak.x

# Forzamos el target para que no intente autodetectar nada
export TARGET = iphone:clang:14.5:14.5
export ARCHS = arm64

include $(THEOS)/makefiles/tweak.mk
