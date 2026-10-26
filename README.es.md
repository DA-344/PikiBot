# PikiBot

**PikiBot**, un bot de Discord modular y extensible desarrollado en Python.

> ❗ **Proyecto en desarrollo**
> PikiBot se encuentra en desarrollo. La estructura, API, y otras partes del proyecto pueden cambiar antes
> de alcanzar una versión estable.

## Estructura Principal del Proyecto

```
PikiBot/
├── Core/     # Implementación principal del bot
├── Modules/  # Módulos y funcionalidades oficiales
├── API/      # API pública para desarrolladores
└── Plugins/  # Plugins y extensiones de terceros
```

### Core

Implementación principal de PikiBot y los componentes necesarios para su funcionamiento.

### Modules

Módulos oficiales que proporcionan funcionalidades adicionales al bot.

### API

Interfaz pública destinada a desarrolladores de extensiones y plugins.

La API está diseñada para permitir una fácil y sencilla comunicación con PikiBot sin necesidad de modificar directamente
su implementación interna.

### Plugins

Los plugins permiten añadir funcionalidades independientes a PikiBot.

Los plugins pueden ser desarrollados y distribuidos de forma independiente al proyecto principal y pueden utilizar sus propios términos y licencias,
siempre que respeten la licencia de PikiBot respecto al código original.

Para más información en como desarrollar plugins, ve a la [Guía de Creación de Plugins](./plugins-guide.md).

## Instalación

> **Instalación mediante PyPI todavía no disponible**

## Versionado

El proyecto intenta seguir [el Versionado Semántico](https://semver.org/lang/es/).

- Una versión MAYOR se lanza cuando se hacen cambios sin compatibilidad a versiones anteriores.
- Una versión MENOR se lanza cuando se añaden funcionalidades con compatibilidad a versiones anteriores bajo la misma versión ``MAYOR``.
- Una versión PARCHE se lanza cuando un arreglo de un bug importante o de emergencia es necesario. 

## Licencia

El código original de PikiBot está disponible bajo la **PikiBot Noncommercial License 1.1.0**.

La licencia permite utilizar, modificar y distribuir el código original para fines no comerciales, sujeto a sus términos y condiciones.

La API pública de PikiBot se encuentra bajo una licencia independiente.

Los plugins y otras contribuciones independientes pueden estar sujetos a sus propias licencias.

Consulta el archivo [`LICENSE.md`](./LICENSE.md) para conocer los términos completos de la licencia del código original.

## Estado del Proyecto

PikiBot está actualmente en desarrollo.

La API, el sistema de plugins, y la estructura interna todavía pueden sufrir cambios importantes.

Por el momento, el proyecto debe considerarse experimental y no se garantiza la estabilidad de la API.
