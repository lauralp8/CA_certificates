# NetApp ONTAP Certificate Management Script

Script automatizado para la gestión completa de certificados digitales (CSR, instalación, modificación SSL y eliminación) en NetApp ONTAP usando la API REST oficial.

## Descripción

Este script de Python automatiza todo el proceso de gestión de certificados digitales en NetApp ONTAP, incluyendo:

- Generación de Certificate Signing Request (CSR) con par de claves
- Instalación de certificados firmados por CA
- Consulta de serial numbers de certificados instalados
- Modificación de configuración SSL
- Eliminación de certificados obsoletos
- Backup automático de event logs del cluster
- Sistema de logging con timestamp para todas las operaciones

## Requisitos

### Software
- Python 3.7 o superior
- NetApp ONTAP 9.6 o superior
- Acceso de red al cluster NetApp
- Credenciales de administrador del cluster

### Dependencias Python
```bash
pip install -r requirements.txt
```

## Estructura del Proyecto

```
CA_certificates/
├── ca_certificates.py                 # Script principal
├── config.yaml                        # Archivo de configuración
├── requirements.txt                   # Dependencias Python
├── README.md                          # Esta documentación
├── csr_certificates/                  # CSR generados automáticamente
│   └── certificate_and_key_*.txt
└── logs/                             # Logs JSON generados automáticamente
    ├── certificate_install_*.json
    ├── serial_numbers_*.json
    ├── ssl_modify_*.json
    ├── certificate_delete_*.json
    ├── security_login_show_*.json
    ├── security_ssl_show_*.json
    └── event_logs_*.json
```

## Configuración

Edita el archivo `config.yaml` con los parámetros de tu entorno. El archivo incluye las siguientes secciones:

### cluster
Configuración de conexión al cluster NetApp:
- `host`: Hostname o IP del cluster
- `username`: Usuario administrador
- `password`: Contraseña

### svm
Configuración de la Storage Virtual Machine:
- `name`: Nombre de la SVM donde gestionar certificados

### certificate
Configuración del certificado digital:
- `common_name`: Nombre común (FQDN) del certificado
- `size`: Tamaño de la clave en bits (2048, 3072, 4096)
- `algorithm`: Algoritmo de cifrado (RSA, EC)
- `hash_function`: Función hash (SHA256, SHA384, SHA512)
- `extended_key_usage`: Lista de usos extendidos ([serverAuth, clientAuth])
- `country`: Código del país (ES, US, UK)
- `state`: Estado o provincia
- `locality`: Ciudad o localidad
- `dns_name`: Nombres DNS alternativos
- `organization`: Nombre de la organización (opcional)
- `organizational_unit`: Unidad organizativa (opcional)
- `email`: Correo electrónico de contacto (opcional)
- `ip`: Direcciones IP alternativas (opcional)
- `uri`: URIs alternativos (opcional)
- `key_usage`: Usos de la clave (opcional)
- `cert_name`: Nombre del certificado en ONTAP (para instalación)
- `type`: Tipo de certificado (server, client, client-ca, server-ca, root-ca)
- `public_certificate_file`: Ruta al archivo con certificado firmado
- `private_key_file`: Ruta al archivo con clave privada

### ssl
Configuración SSL:
- `ca_name`: Nombre de la CA
- `server_enabled`: Habilitar/deshabilitar servidor SSL (true/false)

Para ver ejemplos de configuración, consulta el archivo `config.yaml` incluido en el proyecto.

## Sistema de Logging

El script implementa un sistema de logging automático que captura datos REALES de la cabina NetApp después de cada operación:

### Características
- **Timestamp automático**: Formato YYYYMMDD_HHMMSS (ej: 20260209_092855)
- **Formato JSON**: Datos estructurados y fáciles de procesar
- **Datos de cabina**: GET real desde ONTAP, no configuración enviada
- **Directorio logs/**: Se crea automáticamente si no existe

### Logs Generados

1. **certificate_and_key_YYYYMMDD_HHMMSS.txt**
   - Certificate Signing Request (CSR)
   - Clave privada generada
   - Parámetros del certificado

2. **certificate_install_YYYYMMDD_HHMMSS.json**
   - Nombre del certificado instalado
   - SVM, tipo, estado
   - Serial number, CA, fecha de expiración

3. **serial_numbers_YYYYMMDD_HHMMSS.json**
   - Lista completa de certificados
   - Serial numbers extraídos
   - Detalles de cada certificado

4. **ssl_modify_YYYYMMDD_HHMMSS.json**
   - Configuración SSL modificada
   - Comando CLI generado
   - Parámetros aplicados

5. **certificate_delete_YYYYMMDD_HHMMSS.json**
   - Certificado eliminado
   - Serial number, tipo, CA
   - Certificados restantes

6. **security_login_show_YYYYMMDD_HHMMSS.json**
   - Información de acceso de seguridad
   - Usuarios y métodos de autenticación
   - Generado después de modificar SSL

7. **security_ssl_show_YYYYMMDD_HHMMSS.json**
   - Configuración SSL actual
   - Certificados asociados a SSL
   - Generado después de modificar SSL

8. **event_logs_YYYYMMDD_HHMMSS.json**
   - Backup de eventos del cluster (últimos 100)
   - Index, timestamp, nodo, severidad, evento

## Uso

### Ejecución Básica
```bash
python ca_certificates.py
```

### Menú Interactivo

El script presenta un menú con las siguientes opciones:

```
======================================================================
  CERTIFICATE MANAGEMENT MENU
======================================================================

[1] Generate Certificate Signing Request (CSR)
[2] Install Signed Certificate
[3] Get Serial Numbers, Modify SSL & Delete Old Certificate
[0] Exit (with event logs backup)
[9] Exit without logs

======================================================================
```

### Flujo de Ejecución - Opción 1: Generar CSR

1. **Carga de configuración** - Lee y valida `config.yaml`
2. **Conexión al cluster** - Establece conexión y verifica credenciales
3. **Generación CSR** - Crea CSR con parámetros configurados → Guarda archivo .txt
4. **Mostrar resultados** - Despliega CSR y clave privada en pantalla
5. **Guardar archivos** - Almacena en `csr_certificates/certificate_and_key_*.txt`

### Flujo de Ejecución - Opción 2: Instalar Certificado

1. **Carga de configuración** - Lee y valida `config.yaml`
2. **Conexión al cluster** - Establece conexión y verifica credenciales
3. **Leer certificado público** - Carga archivo especificado en config
4. **Leer clave privada** - Carga archivo con clave privada
5. **Instalación** - POST a API REST de ONTAP → Guarda log
6. **Verificación** - Consulta certificado instalado y muestra detalles

### Flujo de Ejecución - Opción 3: Workflow Completo

1. **Obtener serial numbers** - Consulta todos los certificados → Guarda log
2. **Modificar SSL** - Configura SSL con segundo certificado → Guarda log
3. **Eliminar certificado antiguo** - Borra primer certificado → Guarda log
4. **Mostrar resultados** - Despliega security login show y security ssl show

## API REST de NetApp

Este script utiliza la **API REST oficial de NetApp ONTAP**:

### Endpoints POST (Creación)
- **POST** `/api/security/certificate_signing_request` - Generación de CSR
- **POST** `/api/security/certificates` - Instalación de certificado firmado

### Endpoints GET (Consulta)
- **GET** `/api/security/certificates` - Consulta de certificados
- **GET** `/api/support/ems/events` - Consulta de event logs

### Endpoints DELETE (Eliminación)
- **DELETE** `/api/security/certificates/{uuid}` - Eliminación de certificado

**Documentación oficial**: [NetApp ONTAP REST API](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)

## Registro de Funciones

### Funciones de Configuración y Utilidades

#### config_loader(path="config.yaml")
Carga y valida el archivo de configuración YAML.
- **Entrada**: Ruta al archivo config.yaml
- **Salida**: Diccionario con configuración o None si falla
- **Validaciones**: Verifica estructura y secciones obligatorias (cluster, svm)

#### save_to_log(operation_name, data)
Guarda datos en archivo JSON con timestamp en carpeta logs/.
- **Entrada**: Nombre de operación y diccionario de datos
- **Salida**: Ruta del archivo creado
- **Formato**: `logs/operacion_YYYYMMDD_HHMMSS.json`

#### cluster_connection(cluster_config)
Establece y verifica conexión con el cluster NetApp ONTAP.
- **Entrada**: Diccionario con host, username, password
- **Salida**: True si conexión exitosa, False si falla
- **Validaciones**: Prueba acceso con consulta al cluster

### Funciones de Gestión de Certificados

#### csr_generate(cert_config)
Genera un Certificate Signing Request (CSR) y par de claves privadas.
- **Entrada**: Configuración de certificado desde config.yaml
- **Salida**: True si se generó, False si error
- **POST**: `/api/security/certificate_signing_request`
- **Archivos**: `csr_certificates/certificate_and_key_*.txt`

#### install_certificate(cert_config, svm_name)
Instala un certificado firmado por CA en la SVM especificada.
- **Entrada**: Configuración de certificado y nombre de SVM
- **Salida**: True si instalación exitosa, False si error
- **POST**: `/api/security/certificates`
- **Log**: `certificate_install_YYYYMMDD_HHMMSS.json`

#### get_serial_numbers(svm_name)
Obtiene y muestra los serial numbers de todos los certificados de una SVM.
- **Entrada**: Nombre de la SVM
- **Salida**: Lista de detalles de certificados o None si error
- **GET**: `/api/security/certificates?svm.name={svm_name}`
- **Log**: `serial_numbers_YYYYMMDD_HHMMSS.json`

#### modify_ssl_certificate(svm_name, serial_number, ssl_config, common_name)
Modifica la configuración SSL de un certificado en ONTAP.
- **Entrada**: Nombre SVM, serial number, configuración SSL, common name
- **Salida**: True si modificación exitosa, False si error
- **Operación**: Genera comando CLI para modificación SSL
- **Log**: `ssl_modify_YYYYMMDD_HHMMSS.json`

#### delete_certificate(svm_name, serial_number, cert_config)
Elimina un certificado de la SVM especificada.
- **Entrada**: Nombre SVM, serial number, configuración de certificado
- **Salida**: True si eliminación exitosa, False si error
- **DELETE**: `/api/security/certificates/{uuid}`
- **Log**: `certificate_delete_YYYYMMDD_HHMMSS.json`

### Funciones de Monitoreo

#### get_event_logs(max_records=100)
Obtiene y respalda los logs de eventos del cluster.
- **Entrada**: Número máximo de registros (default: 100)
- **Salida**: True si se obtuvieron, False si error
- **GET**: `/api/support/ems/events`
- **Log**: `event_logs_YYYYMMDD_HHMMSS.json`

### Funciones de Menú

#### display_menu()
Muestra el menú principal de opciones interactivas.
- **Entrada**: Ninguna
- **Salida**: Menú en pantalla

#### execute_option(option, config_data)
Ejecuta la opción seleccionada del menú.
- **Entrada**: Número de opción y datos de configuración
- **Salida**: True para continuar, False para salir

## Registro de Errores

### Errores de Configuración

#### ERR-001: Archivo de configuración no encontrado
```
[ERROR] File not found: config.yaml
```
**Causa**: El archivo config.yaml no existe en el directorio actual  
**Solución**: Verificar que config.yaml existe en la misma carpeta que el script

#### ERR-002: YAML inválido
```
[ERROR] Invalid YAML format in 'config.yaml'
```
**Causa**: Sintaxis YAML incorrecta (indentación, formato)  
**Solución**: Validar sintaxis YAML, verificar espacios e indentación

#### ERR-003: Configuración incompleta
```
[ERROR] Incomplete configuration: missing 'cluster' section
[ERROR] Incomplete configuration: missing 'svm' section
```
**Causa**: Faltan secciones obligatorias en config.yaml  
**Solución**: Asegurar que config.yaml contenga secciones 'cluster' y 'svm'

#### ERR-004: Campos obligatorios faltantes
```
[ERROR] Missing required fields in cluster config: host, username
[ERROR] Missing required fields in certificate config: common_name, size
```
**Causa**: Faltan campos obligatorios en la configuración  
**Solución**: Completar todos los campos requeridos

### Errores de Conexión

#### ERR-101: Error de autenticación
```
[ERROR] HTTP status: 401
[ERROR] Authentication failed
[ERROR] Invalid username or password
```
**Causa**: Credenciales incorrectas  
**Solución**: Verificar username y password en config.yaml

#### ERR-102: Acceso denegado
```
[ERROR] HTTP status: 403
[ERROR] Forbidden - User lacks required permissions
```
**Causa**: Usuario sin permisos de administrador  
**Solución**: Usar cuenta con rol admin o vsadmin

#### ERR-103: Host no alcanzable
```
[ERROR] Cannot reach host 'cluster1.demo.netapp.com'
```
**Causa**: Problemas de red o hostname incorrecto  
**Solución**: Verificar conectividad de red y hostname/IP del cluster

#### ERR-104: Timeout de conexión
```
[ERROR] Connection timeout to 'cluster1.demo.netapp.com'
```
**Causa**: Cluster no responde  
**Solución**: Verificar que el cluster esté encendido y accesible

### Errores de Generación CSR

#### ERR-201: Parámetros de certificado inválidos
```
[ERROR] Bad request - Check certificate parameters
```
**Causa**: Parámetros de certificado incorrectos o incompatibles  
**Solución**: Revisar common_name, size, algorithm, hash_function en config.yaml

#### ERR-202: Tamaño de clave no soportado
```
[ERROR] Invalid key size
```
**Causa**: Tamaño de clave no válido  
**Solución**: Usar tamaños estándar: 2048, 3072, 4096, 7680

#### ERR-203: Algoritmo no soportado
```
[ERROR] Invalid algorithm
```
**Causa**: Algoritmo de cifrado no válido  
**Solución**: Usar algoritmos soportados: RSA, EC

#### ERR-204: Función hash no válida
```
[ERROR] Invalid hash function
```
**Causa**: Función hash no soportada  
**Solución**: Usar funciones válidas: SHA256, SHA384, SHA512

### Errores de Instalación de Certificados

#### ERR-301: Archivo de certificado no encontrado
```
[ERROR] Public certificate file not found: certificate.pem
[ERROR] Private key file not found: private_key.pem
```
**Causa**: Los archivos especificados no existen  
**Solución**: Verificar rutas en config.yaml y que archivos existan

#### ERR-302: Formato de certificado inválido
```
[ERROR] Bad Request - Invalid certificate format or parameters
```
**Causa**: Certificado o clave privada en formato incorrecto  
**Solución**: Asegurar que archivos estén en formato PEM válido

#### ERR-303: Certificado ya existe
```
[ERROR] Conflict - Certificate with this name already exists
```
**Causa**: Ya existe un certificado con ese nombre  
**Solución**: Cambiar cert_name en config.yaml o eliminar certificado existente

#### ERR-304: Certificado y clave no coinciden
```
[ERROR] Unprocessable Entity - Certificate validation failed
```
**Causa**: El certificado público no corresponde a la clave privada  
**Solución**: Verificar que certificado y clave sean un par válido

### Errores de Serial Numbers

#### ERR-401: SVM no encontrada
```
[ERROR] Not Found - SVM may not exist
```
**Causa**: La SVM especificada no existe en el cluster  
**Solución**: Verificar nombre de SVM con `vserver show`

#### ERR-402: Sin permisos para consultar certificados
```
[ERROR] Forbidden - User lacks required permissions
```
**Causa**: Usuario sin permisos de lectura en security  
**Solución**: Asignar permisos de lectura en security al usuario

#### ERR-403: No se encontraron certificados
```
[WARNING] No serial numbers found in any certificate
```
**Causa**: No hay certificados instalados en la SVM  
**Solución**: Instalar al menos un certificado antes de consultar

### Errores de Modificación SSL

#### ERR-501: Certificado no encontrado para SSL
```
[WARNING] Certificate not found with serial number: 1234567890
```
**Causa**: El serial number no corresponde a ningún certificado  
**Solución**: Verificar serial number con get_serial_numbers

#### ERR-502: Configuración SSL incompleta
```
[ERROR] Missing required fields in config.yaml under 'ssl' section
```
**Causa**: Faltan campos ca_name o server_enabled  
**Solución**: Agregar campos requeridos en sección ssl de config.yaml

### Errores de Eliminación de Certificados

#### ERR-601: Certificado no existe
```
[ERROR] Not Found - Certificate does not exist
```
**Causa**: El certificado ya fue eliminado o no existe  
**Solución**: Verificar certificados existentes con get_serial_numbers

#### ERR-602: Certificado en uso
```
[ERROR] Conflict - Certificate may be in use
```
**Causa**: El certificado está asignado a configuración SSL activa  
**Solución**: Modificar SSL para usar otro certificado antes de eliminar

### Errores de Event Logs

#### ERR-701: No se pueden obtener event logs
```
[WARNING] Event logs backup failed (non-critical)
```
**Causa**: Error al consultar API de eventos  
**Solución**: No crítico, verificar permisos de lectura de eventos

### Códigos de Estado HTTP Comunes

- **400 Bad Request**: Parámetros inválidos en la solicitud
- **401 Unauthorized**: Credenciales incorrectas
- **403 Forbidden**: Sin permisos suficientes
- **404 Not Found**: Recurso no existe
- **409 Conflict**: Recurso ya existe o conflicto de estado
- **422 Unprocessable Entity**: Validación de datos falló
- **500 Internal Server Error**: Error interno del servidor ONTAP

## Seguridad

- **IMPORTANTE**: NO compartas el archivo `config.yaml` con credenciales
- Considera usar variables de entorno para credenciales sensibles
- El script desactiva verificación SSL (`verify=False`) - úsalo solo en entornos de desarrollo/pruebas
- Los logs pueden contener información sensible - protege el directorio `logs/`
- **La clave privada generada es MUY SENSIBLE** - guárdala en un lugar seguro y elimínala del directorio después de la instalación

## Licencia

Este script es para uso interno y educativo.

## Soporte

Para problemas relacionados con la API de NetApp, consulta:
- [Documentación API REST](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)
- [NetApp Community](https://community.netapp.com/)
- [Python Client Library](https://pypi.org/project/netapp-ontap/)

---

**Versión**: 1.0  
**Última actualización**: Febrero 2026  
**Compatible con**: ONTAP 9.6+
