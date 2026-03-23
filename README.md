# NetApp ONTAP Certificate Management Script

Script automatizado para la gestión completa de certificados digitales en NetApp ONTAP usando la API REST oficial.

## Índice

- [Descripción](#descripción)
- [Requisitos](#requisitos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Guía de Configuración Inicial](#guía-de-configuración-inicial)
- [Referencia de Parámetros](#referencia-de-parámetros)
- [Referencia de Funciones](#referencia-de-funciones)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Registro de Errores](#registro-de-errores)
- [Sistema de Logging](#sistema-de-logging)
- [Seguridad y Buenas Prácticas](#seguridad-y-buenas-prácticas)

## Descripción

Este script automatiza el ciclo de vida completo de certificados digitales en NetApp ONTAP usando la API REST oficial. Proporciona una solución integral para gestionar certificados SSL/TLS en entornos empresariales, desde la generación inicial hasta la renovación y eliminación.

### Funcionalidades Principales

**1. Generación de Certificate Signing Request (CSR)**
- Creación automática de CSR y pares de claves privadas
- Soporte para RSA (2048, 3072, 4096 bits) y EC
- Funciones hash: SHA256, SHA384, SHA512
- Subject Alternative Names (SAN): DNS, email, IP, URI
- Extended Key Usage: serverAuth, clientAuth
- Key Usage: digitalSignature, keyEncipherment, etc.

**2. Instalación de Certificados Firmados**
- Instalación de certificados públicos firmados por CA externa
- Lectura automática de archivos PEM
- Validación de certificados y claves privadas
- Verificación de instalación con GET después de POST

**3. Modificación de Configuración SSL**
- Actualización de configuración SSL de la SVM
- Asignación de certificados instalados a servicios
- Uso de API privada CLI para comandos avanzados
- Verificación de cambios aplicados

**4. Eliminación de Certificados Obsoletos**
- Eliminación controlada de certificados antiguos
- Validación de certificados no en uso
- Limpieza de certificados autofirmados (CA = SVM name)

**5. Consulta de Serial Numbers**
- Listado de todos los certificados de una SVM
- Extracción de serial numbers, CA, CN, expiry dates
- Identificación de certificados instalados vs autofirmados

**6. Menú Interactivo**
- 3 opciones principales + 2 de salida
- Workflow guiado paso a paso
- Backup automático de event logs al salir

### Casos de Uso

- **Renovación de Certificados**: Generar CSR → Enviar a CA → Instalar certificado → Modificar SSL → Eliminar antiguo
- **Primera Configuración SSL**: Configurar certificados en SVM nueva
- **Auditoría de Certificados**: Consultar certificados instalados y fechas de expiración
- **Preparación para Producción**: Reemplazar certificados autofirmados por certificados enterprise

## Requisitos

### Software

- **Python**: 3.7 o superior (desarrollado y probado con 3.11.4)
- **NetApp ONTAP**: 9.6 o superior (desarrollado para 9.15.1)
- **Git**: Para clonar repositorio (opcional)

### Dependencias Python

Instalar todas las dependencias con:

```bash
pip install -r requirements.txt
```

**Librerías principales:**
- `netapp-ontap >= 9.14.0`: Python Client Library oficial de NetApp para ONTAP REST API
- `PyYAML >= 6.0`: Parser para archivos de configuración YAML
- `requests`: Cliente HTTP para llamadas REST
- `urllib3`: Manejo de conexiones HTTP/HTTPS

### Requisitos de Red y Conectividad

**Conectividad:**
- Acceso HTTPS (puerto 443) al cluster management interface
- Resolución DNS del hostname del cluster (o uso de IP directa)
- Sin firewalls bloqueando la comunicación

**Certificados SSL:**
- El script desactiva la verificación SSL (`verify=False`) por defecto
- Para entornos productivos, considerar verificación SSL habilitada

### Permisos y Roles ONTAP

**Permisos mínimos requeridos:**
- `security certificate create`: Crear certificados
- `security certificate install`: Instalar certificados
- `security certificate show`: Consultar certificados
- `security certificate delete`: Eliminar certificados
- `security ssl modify`: Modificar configuración SSL
- `event log show`: Consultar event logs

**Roles recomendados:**
- `admin`: Acceso completo (recomendado para pruebas)
- `security`: Rol específico para operaciones de seguridad

### Archivos Necesarios para Instalación

Para la opción 2 (Install Certificate), necesitas:
1. **Certificado público** (.crt, .pem): Certificado firmado por tu CA
2. **Clave privada** (.key, .pem): Clave privada generada con el CSR

Ambos archivos deben estar en formato PEM (texto con `-----BEGIN...-----`).

## Estructura del Proyecto

```
CA_certificates/
├── ca_certificates.py
├── config.yaml
├── requirements.txt
├── README.md
├── csr_certificates/
└── logs/
```

## Guía de Configuración Inicial

### Paso 1: Crear config.yaml desde Cero

Crea un archivo `config.yaml` en el directorio raíz del script con la siguiente estructura:

```yaml
# ============================================================================
# NETAPP ONTAP CONFIGURATION FILE - Certificate Management
# ============================================================================

# CONFIGURACIÓN DE CONEXIÓN AL CLÚSTER
cluster:
  host: 10.0.0.100                    # IP o hostname del cluster
  username: admin                      # Usuario con permisos de seguridad
  password: MySecurePassword123        # Contraseña del usuario

# CONFIGURACIÓN SVM
svm:
  name: svm_production_01              # Nombre de la SVM donde gestionar certificados

# CONFIGURACIÓN DE CERTIFICADOS
certificate:
  # ====================================================================
  # GENERACIÓN DE CSR (Opción 1)
  # ====================================================================
  common_name: nas01.company.com       # FQDN del servidor (REQUERIDO)
  size: 2048                           # Tamaño de clave: 2048, 3072, 4096 bits
  algorithm: RSA                       # Algoritmo: RSA o EC
  hash_function: SHA256                # Hash: SHA256, SHA384, SHA512
  
  # Subject del certificado (Distinguished Name)
  country: ES                          # Código país (2 letras - REQUERIDO)
  state: Madrid                        # Provincia/Estado (REQUERIDO)
  locality: Madrid                     # Ciudad (REQUERIDO)
  
  # Subject Alternative Names (SAN) - Opcional
  dns_name: nas01.company.com          # DNS alternativo(s)
  # dns_name:                          # También puede ser lista:
  #   - nas01.company.com
  #   - nas01-alt.company.com
  
  # Extended Key Usage - Opcional
  extended_key_usage:
    - serverAuth                       # Autenticación servidor
    - clientAuth                       # Autenticación cliente
  
  # Campos opcionales del subject
  # organization: My Company SA
  # organizational_unit: IT Department
  # email: admin@company.com
  
  # Subject Alternative Names adicionales (opcional)
  # ip:
  #   - 10.0.0.100
  # uri:
  #   - https://nas01.company.com
  
  # Key Usage (opcional)
  # key_usage:
  #   - digitalSignature
  #   - keyEncipherment
  
  # ====================================================================
  # INSTALACIÓN DE CERTIFICADOS (Opción 2)
  # ====================================================================
  cert_name: production_cert           # Nombre del certificado en ONTAP
  type: server                         # Tipo: server, client, client-ca, server-ca, root-ca
  
  # Rutas a los archivos (relativas o absolutas)
  public_certificate_file: certificates/server_cert.crt    # Certificado público
  private_key_file: certificates/private_key.key           # Clave privada

# CONFIGURACIÓN SSL (Opción 3)
ssl:
  server_enabled: true                 # Habilitar SSL en servidor: true/false
```

### Paso 2: Ajustar Configuración según Opción

**Para Opción 1 - Generar CSR:**
- Completa todos los campos bajo `certificate` relacionados con CSR
- El script generará el CSR y la clave privada
- Guarda el CSR generado en `csr_certificates/`

**Para Opción 2 - Instalar Certificado:**
- Asegúrate de tener el certificado firmado por tu CA
- Actualiza `public_certificate_file` con la ruta al certificado
- Actualiza `private_key_file` con la ruta a la clave privada
- Verifica que `cert_name` sea único en la SVM

**Para Opción 3 - Modificar SSL y Eliminar:**
- Configura `ssl.server_enabled` según necesites
- El script automáticamente identificará certificados a usar/eliminar
- Usa el certificado instalado (CA ≠ nombre SVM)
- Elimina el certificado autofirmado (CA = nombre SVM)

### Paso 3: Valores por Defecto y Recomendaciones

| Campo | Valor Recomendado | Notas |
|-------|-------------------|-------|
| `size` | 2048 o 3072 | 2048 suficiente para mayoría; 4096 mayor seguridad |
| `algorithm` | RSA | RSA soportado universalmente; EC más eficiente |
| `hash_function` | SHA256 | SHA384/512 para mayor seguridad |
| `type` | server | Para certificados de servicios NFS/CIFS/iSCSI |
| `server_enabled` | true | Habilitar SSL en servidor |

### Ejemplo Completo: Workflow de Renovación

```yaml
# Configuración para renovar certificado de producción
cluster:
  host: cluster-prod.company.com
  username: security_admin
  password: <PASSWORD>

svm:
  name: svm_nas_production

certificate:
  # Paso 1: Generar nuevo CSR
  common_name: nas-prod.company.com
  size: 3072
  algorithm: RSA
  hash_function: SHA384
  country: ES
  state: Barcelona
  locality: Barcelona
  dns_name:
    - nas-prod.company.com
    - nas-prod-dr.company.com
  extended_key_usage:
    - serverAuth
  
  # Paso 2: Después de recibir certificado de CA
  cert_name: nas_prod_2026
  type: server
  public_certificate_file: /certs/nas_prod_2026.crt
  private_key_file: /certs/nas_prod_2026.key

ssl:
  server_enabled: true
```

## Referencia de Parámetros

### Sección cluster

Configuración de conexión al cluster NetApp ONTAP.

- **host** (string, requerido)
  - IP o hostname del cluster management interface
  - Ejemplo: `10.0.0.100` o `cluster1.demo.netapp.com`
  - Debe ser accesible por HTTPS (puerto 443)

- **username** (string, requerido)
  - Usuario con permisos de administración de certificados
  - Roles válidos: `admin`, `security`
  - Ejemplo: `admin` o `security_admin`

- **password** (string, requerido)
  - Contraseña del usuario
  - **CRÍTICO**: NO subir a repositorios públicos
  - Usar variables de entorno en producción

### Sección svm

Identificación de la Storage Virtual Machine (SVM) donde gestionar certificados.

- **name** (string, requerido)
  - Nombre exacto de la SVM en ONTAP
  - Distingue mayúsculas/minúsculas
  - Verificar con: `vserver show` en CLI
  - Ejemplo: `svm_production_01`

### Sección certificate

Parámetros para generación de CSR e instalación de certificados.

#### Parámetros de Generación de CSR

**Campos básicos del certificado:**

- **common_name** (string, requerido)
  - FQDN (Fully Qualified Domain Name) del servidor
  - Debe coincidir con el nombre que usarán los clientes
  - Ejemplo: `nas01.company.com`
  - **IMPORTANTE**: Este será el CN del Subject

- **size** (integer, requerido)
  - Tamaño de la clave en bits
  - Valores válidos: `2048`, `3072`, `4096`, `7680`
  - Recomendado: `2048` (compatibilidad), `3072` (seguridad mejorada)
  - Mapeo interno a security_strength:
    - 2048 bits → 112
    - 3072 bits → 128
    - 7680 bits → 192

- **algorithm** (string, requerido)
  - Algoritmo de cifrado de la clave
  - Valores válidos: `RSA`, `EC` (Elliptic Curve)
  - Recomendado: `RSA` (compatibilidad universal)
  - Nota: El script convierte a minúsculas automáticamente

- **hash_function** (string, requerido)
  - Función hash para firmar el CSR
  - Valores válidos: `SHA256`, `SHA384`, `SHA512`
  - Recomendado: `SHA256` (balance seguridad/performance)
  - `SHA384`/`SHA512`: Mayor seguridad para entornos críticos

**Subject del certificado (Distinguished Name):**

- **country** (string, requerido)
  - Código ISO del país (2 letras)
  - Ejemplo: `ES`, `US`, `FR`, `DE`
  - **IMPORTANTE**: Debe ser exactamente 2 caracteres

- **state** (string, requerido)
  - Provincia o estado
  - Ejemplo: `Madrid`, `Barcelona`, `California`
  - Sin acentos en el texto

- **locality** (string, requerido)
  - Ciudad o localidad
  - Ejemplo: `Madrid`, `Barcelona`, `San Francisco`

- **organization** (string, opcional)
  - Nombre de la organización
  - Ejemplo: `My Company SA`, `Acme Corporation`

- **organizational_unit** (string, opcional)
  - Departamento o unidad organizativa
  - Ejemplo: `IT Department`, `Storage Team`

- **email** (string, opcional)
  - Email de contacto del administrador
  - Ejemplo: `admin@company.com`

**Subject Alternative Names (SAN):**

- **dns_name** (string o list, opcional)
  - Nombres DNS alternativos del servidor
  - Puede ser string único: `nas01.company.com`
  - O lista: `["nas01.company.com", "nas01-alt.company.com"]`
  - Útil para servidores con múltiples nombres DNS

- **ip** (list, opcional)
  - Direcciones IP alternativas
  - Formato: `["10.0.0.100", "10.0.0.101"]`
  - Poco común en entornos enterprise

- **uri** (list, opcional)
  - URIs alternativos
  - Formato: `["https://nas01.company.com"]`

**Extended Key Usage:**

- **extended_key_usage** (list, opcional)
  - Define propósitos permitidos del certificado
  - Valores válidos:
    - `serverAuth`: Autenticación de servidor (HTTPS, TLS server)
    - `clientAuth`: Autenticación de cliente (TLS client)
    - `codeSigning`: Firma de código
    - `emailProtection`: Protección de correo S/MIME
  - Ejemplo: `["serverAuth", "clientAuth"]`
  - **NOTA**: No soportado directamente en API de CSR, configurar en CA

**Key Usage:**

- **key_usage** (list, opcional)
  - Operaciones criptográficas permitidas
  - Valores válidos:
    - `digitalSignature`: Firma digital
    - `keyEncipherment`: Cifrado de claves
    - `dataEncipherment`: Cifrado de datos
    - `keyAgreement`: Acuerdo de claves
    - `keyCertSign`: Firma de certificados
    - `cRLSign`: Firma de CRLs
  - Ejemplo: `["digitalSignature", "keyEncipherment"]`

#### Parámetros de Instalación de Certificados

- **cert_name** (string, requerido)
  - Nombre del certificado en ONTAP
  - Debe ser único en la SVM
  - Ejemplo: `production_cert_2026`
  - Convención sugerida: `<purpose>_<year>`

- **type** (string, requerido)
  - Tipo de certificado
  - Valores válidos:
    - `server`: Certificado de servidor (más común)
    - `client`: Certificado de cliente
    - `client-ca`: CA de certificados de cliente
    - `server-ca`: CA de certificados de servidor
    - `root-ca`: CA raíz
  - Para servicios NAS/SAN: usar `server`

- **public_certificate_file** (string, requerido)
  - Ruta al archivo del certificado público
  - Formato: PEM (texto con `-----BEGIN CERTIFICATE-----`)
  - Puede ser ruta relativa: `certs/server.crt`
  - O absoluta: `C:\certificates\server.crt`

- **private_key_file** (string, requerido)
  - Ruta al archivo de la clave privada
  - Formato: PEM (texto con `-----BEGIN PRIVATE KEY-----`)
  - Debe corresponder al certificado público
  - **CRÍTICO**: Proteger con permisos restrictivos (chmod 600)

### Sección ssl

Configuración SSL de la SVM.

- **server_enabled** (boolean, requerido para opción 3)
  - Habilitar o deshabilitar servidor SSL
  - Valores: `true` (habilitar), `false` (deshabilitar)
  - Para producción: siempre `true`
  - Afecta a protocolos NFS, CIFS, HTTP

## Referencia de Funciones

### config_loader

```python
def config_loader(path="config.yaml") -> dict | None
```

**Descripción:**  
Carga y valida el archivo de configuración YAML con las credenciales del cluster y parámetros de certificados.

**Parámetros:**
- `path` (str, opcional): Ruta al archivo YAML. Default: `"config.yaml"`

**Retorna:**
- `dict`: Diccionario con la configuración si es válida
- `None`: Si el archivo no existe, está mal formado o faltan secciones requeridas

**Validaciones realizadas:**
- Archivo existe y es legible
- YAML válido (sintaxis correcta)
- Contiene sección `cluster` con `host`, `username`, `password`
- Contiene sección `svm` con `name`

**Uso interno:**  
Llamada al inicio de cada opción del menú para cargar la configuración actualizada.

**Errores manejados:**
- `FileNotFoundError`: Archivo no encontrado
- `yaml.YAMLError`: Sintaxis YAML inválida
- `PermissionError`: Sin permisos de lectura

---

### save_to_log

```python
def save_to_log(operation_name: str, data: dict) -> str
```

**Descripción:**  
Guarda datos en un archivo JSON dentro de la carpeta `logs/` con timestamp automático.

**Parámetros:**
- `operation_name` (str): Nombre de la operación (ej: `'certificate_install'`, `'ssl_modify'`)
- `data` (dict): Diccionario con los datos a guardar (normalmente resultado de GET)

**Retorna:**
- `str`: Ruta del archivo creado (ej: `logs/certificate_install_20260312_143025.json`)
- `None`: Si falla la escritura

**Formato del nombre:**  
`{operation_name}_{YYYYMMDD}_{HHMMSS}.json`

**Uso interno:**  
Llamada después de cada operación exitosa para guardar el estado actual del recurso.

---

### cluster_connection

```python
def cluster_connection(cluster_config: dict) -> bool
```

**Descripción:**  
Establece conexión con el cluster NetApp ONTAP y verifica acceso mediante consulta al objeto `Cluster`.

**Parámetros:**
- `cluster_config` (dict): Diccionario con claves:
  - `host` (str): IP o hostname del cluster
  - `username` (str): Usuario
  - `password` (str): Contraseña

**Retorna:**
- `True`: Conexión exitosa y acceso verificado
- `False`: Fallo en conexión o autenticación

**Operaciones realizadas:**
1. Valida presencia de campos requeridos
2. Establece `config.CONNECTION` con `HostConnection`
3. Ejecuta `Cluster().get()` para verificar acceso
4. Muestra nombre del cluster y versión ONTAP

**Errores manejados:**
- `NetAppRestError`: Errores HTTP (401, 403, 404)
- `ConnectionError`: Host no alcanzable
- `TimeoutError`: Timeout de conexión

**Uso interno:**  
Primera función llamada en cada opción del menú antes de cualquier operación.

---

### csr_generate

```python
def csr_generate(cert_config: dict) -> bool
```

**Descripción:**  
Genera un Certificate Signing Request (CSR) y un par de claves privadas usando la API REST de NetApp ONTAP. Guarda el CSR y la clave en `csr_certificates/`.

**Parámetros:**
- `cert_config` (dict): Configuración del certificado con campos:
  - `common_name`, `size`, `algorithm`, `hash_function`
  - `country`, `state`, `locality`
  - `organization`, `organizational_unit`, `email` (opcionales)
  - `dns_name`, `ip`, `uri` (opcionales, SAN)
  - `extended_key_usage`, `key_usage` (opcionales)

**Retorna:**
- `True`: CSR generado exitosamente
- `False`: Fallo en generación

**Operaciones realizadas:**
1. Valida campos requeridos
2. Construye Subject Name en formato Distinguished Name (DN)
   - Formato: `C=ES,ST=Madrid,L=Madrid,O=Company,OU=IT,CN=nas01.company.com`
3. Mapea `size` a `security_strength` (2048→112, 3072→128, 7680→192)
4. Construye body con Subject Alternative Names
5. POST a `/api/security/certificate-signing-request`
6. Extrae CSR y clave privada de la respuesta
7. Guarda en `csr_certificates/certificate_and_key_{timestamp}.txt`
8. Guarda metadatos en `logs/certificate_csr_{timestamp}.json`

**Endpoint API:**  
`POST /api/security/certificate-signing-request`

**Errores manejados:**
- `NetAppRestError`: Errores HTTP (400 parámetros inválidos, 403 permisos)
- `KeyError`: Campos faltantes en respuesta
- Validación: Campos requeridos vacíos

**Uso interno:**  
Invocada por la opción 1 del menú.

---

### install_certificate

```python
def install_certificate(cert_config: dict, svm_name: str) -> bool
```

**Descripción:**  
Instala un certificado firmado por CA en la SVM especificada. Lee los archivos PEM de certificado público y clave privada, y los instala usando la API privada CLI de ONTAP.

**Parámetros:**
- `cert_config` (dict): Configuración con:
  - `cert_name` (str): Nombre del certificado en ONTAP
  - `type` (str): Tipo (`server`, `client`, etc.)
  - `public_certificate_file` (str): Ruta al certificado público
  - `private_key_file` (str): Ruta a la clave privada
- `svm_name` (str): Nombre de la SVM

**Retorna:**
- `True`: Instalación exitosa
- `False`: Fallo en instalación

**Operaciones realizadas:**
1. Valida parámetros de configuración
2. Lee contenido de certificado público desde archivo
3. Lee contenido de clave privada desde archivo
4. Construye comando CLI: `security certificate install -vserver X -type server`
5. POST a `/api/private/cli/security/certificate` con:
   - Certificado público
   - Clave privada
   - `continue_input: "n"` (no agregar certificados intermedios)
6. GET del certificado instalado para verificación
7. Guarda log en `logs/certificate_install_{timestamp}.json`

**Endpoint API:**  
`POST /api/private/cli/security/certificate`

**Formato archivos esperado:**
```
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKL...
-----END CERTIFICATE-----

-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0...
-----END PRIVATE KEY-----
```

**Errores manejados:**
- `FileNotFoundError`: Archivos de certificado no encontrados
- `NetAppRestError`: HTTP 409 (certificado existe), 422 (validación fallida)
- Validación: Certificado y clave no coinciden

**Uso interno:**  
Invocada por la opción 2 del menú.

---

### get_serial_numbers

```python
def get_serial_numbers(svm_name: str) -> list | None
```

**Descripción:**  
Obtiene y muestra los serial numbers y detalles de todos los certificados de una SVM específica.

**Parámetros:**
- `svm_name` (str): Nombre de la SVM a consultar

**Retorna:**
- `list`: Lista de diccionarios con detalles de certificados:
  ```python
  [
    {
      "certificate_name": "rhoso",
      "common_name": "nas01.company.com",
      "serial_number": "7BB05FC50001000001E2",
      "type": "server",
      "ca": "vdc-ca",
      "expiry_time": "2028-02-24T17:32:32+01:00",
      "uuid": "4ff70002-13e1-11f1-a019-d039eaccfdc5"
    }
  ]
  ```
- `None`: Si no hay certificados o falla la consulta

**Operaciones realizadas:**
1. GET a `/api/security/certificates` filtrando por `svm.name`
2. Extrae campos: name, common_name, serial_number, type, ca, expiry_time, uuid
3. Muestra tabla formateada en consola
4. Guarda en `logs/serial_numbers_{timestamp}.json`

**Endpoint API:**  
`GET /api/security/certificates?svm.name={svm_name}&fields=*`

**Uso interno:**  
- Invocada por la opción 3 para identificar certificados
- También usada para auditoría de certificados instalados

---

### modify_ssl_certificate

```python
def modify_ssl_certificate(svm_name: str, serial_number: str, 
                          ssl_config: dict, common_name: str, 
                          ca_name: str = None) -> bool
```

**Descripción:**  
Modifica la configuración SSL de una SVM para usar un certificado específico. Utiliza la API privada CLI porque la configuración SSL no está completamente soportada en la API REST pública.

**Parámetros:**
- `svm_name` (str): Nombre de la SVM
- `serial_number` (str): Serial number del certificado a usar
- `ssl_config` (dict): Configuración SSL con `server_enabled` (bool)
- `common_name` (str): Common Name del certificado
- `ca_name` (str, opcional): Nombre de la CA. Si es None, se extrae automáticamente

**Retorna:**
- `True`: Modificación SSL exitosa
- `False`: Fallo en modificación

**Operaciones realizadas:**
1. Valida `server_enabled` en `ssl_config`
2. Si no se proporciona `ca_name`, lo extrae del certificado usando `SecurityCertificate.find()`
3. Construye comando CLI: `security ssl modify -vserver X -server-enabled true -ca Y -serial Z -common-name W`
4. POST a `/api/private/cli/security/ssl` con parámetros
5. GET de verificación: `/api/private/cli/security/ssl?vserver={svm_name}`
6. Guarda log en `logs/ssl_modify_{timestamp}.json`

**Endpoint API:**  
- `POST /api/private/cli/security/ssl`
- `GET /api/private/cli/security/ssl?vserver={svm_name}`

**Comando CLI equivalente:**
```bash
security ssl modify -vserver svm_production_01 \
  -server-enabled true \
  -ca vdc-ca \
  -serial 7BB05FC50001000001E2 \
  -common-name nas01.company.com
```

**Errores manejados:**
- `NetAppRestError`: HTTP 404 (certificado no encontrado), 400 (parámetros inválidos)
- Validación: CA name no extraíble

**Uso interno:**  
Invocada por la opción 3 (primer paso del workflow combinado).

---

### delete_certificate

```python
def delete_certificate(svm_name: str, serial_number: str, 
                      cert_config: dict) -> bool
```

**Descripción:**  
Elimina un certificado específico de una SVM. Valida que el certificado no esté en uso antes de eliminarlo.

**Parámetros:**
- `svm_name` (str): Nombre de la SVM
- `serial_number` (str): Serial number del certificado a eliminar
- `cert_config` (dict): Configuración con:
  - `type` (str): Tipo de certificado
  - `common_name` (str): Common name
  - `ca_name` (str): Nombre de la CA

**Retorna:**
- `True`: Certificado eliminado exitosamente
- `False`: Fallo en eliminación

**Operaciones realizadas:**
1. Busca el certificado usando `SecurityCertificate.find()` con filtros:
   - `svm.name`
   - `serial_number`
2. Si se encuentra, ejecuta `certificate_obj.delete()`
3. Verifica eliminación intentando GET del certificado
4. Guarda log en `logs/certificate_delete_{timestamp}.json`

**Endpoint API:**  
`DELETE /api/security/certificates/{uuid}`

**Errores manejados:**
- `NetAppRestError`: HTTP 404 (certificado no existe), 409 (certificado en uso)
- Validación: Certificado no encontrado

**Uso interno:**  
Invocada por la opción 3 (segundo paso del workflow combinado).

---

### get_event_logs

```python
def get_event_logs(max_records: int = 100) -> bool
```

**Descripción:**  
Obtiene los event logs del cluster relacionados con operaciones de seguridad y certificados.

**Parámetros:**
- `max_records` (int, opcional): Número máximo de logs a recuperar. Default: `100`

**Retorna:**
- `True`: Logs obtenidos exitosamente
- `False`: Fallo en obtención

**Operaciones realizadas:**
1. GET a `/api/support/ems/events` con `max_records`
2. Extrae campos relevantes de cada evento
3. Guarda en `logs/event_logs_{timestamp}.json`

**Endpoint API:**  
`GET /api/support/ems/events?max_records={max_records}`

**Uso interno:**  
Invocada al salir del script con opción 0 para backup de auditoría.

## Ejemplos de Uso

### Ejecución del Script

```bash
python ca_certificates.py
```

### Menú Interactivo

Al ejecutar el script, verás el siguiente menú:

```
======================================================================
  NetApp ONTAP Certificate Management Script
  Using NetApp ONTAP Python Client Library
======================================================================

[*] Initializing Certificate Signing Request workflow...

======================================================================
  CERTIFICATE MANAGEMENT MENU
======================================================================

[1] Generate Certificate Signing Request (CSR)
[2] Install Signed Certificate
[3] Modify SSL and Delete Certificate
[0] Exit (with event logs backup)
[9] Exit without logs

======================================================================
Select an option:
```

---

### Opción 1: Generar Certificate Signing Request (CSR)

**Workflow completo:**

```
Select an option: 1

[*] Starting CSR generation workflow...
[+] Config.yaml loader: config.yaml
[+] Configuration loaded successfully
[+] Target cluster: cluster1.demo.netapp.com
[+] SVM to create: svm_production_01

[*] Establishing connection to cluster: cluster1.demo.netapp.com
[+] Connection successful!
[+] Cluster name: cluster1
[+] ONTAP version: NetApp Release 9.15.1: Tue Jan 09 00:58:09 UTC 2024

[*] Generating Certificate Signing Request (CSR)...
[+] Certificate details:
    - Common Name: nas01.company.com
    - Subject: C=ES,ST=Madrid,L=Madrid,CN=nas01.company.com
    - Algorithm: RSA
    - Key Size: 2048 bits
    - Hash Function: SHA256
    - DNS Names: nas01.company.com

[*] Calling NetApp API to generate CSR...
[+] CSR generated successfully!
[+] Created directory: csr_certificates/

[+] Certificate Signing Request (CSR):
======================================================================
-----BEGIN CERTIFICATE REQUEST-----
MIICwjCCAaoCAQAwfzELMAkGA1UEBhMCRVMxDzANBgNVBAgTBk1hZHJpZDEPMA0G
A1UEBxMGTWFkcmlkMRwwGgYDVQQDExNuYXMwMS5jb21wYW55LmNvbTEwMC4GA1UE
BRMHY29tcGFueTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAL4K3x...
-----END CERTIFICATE REQUEST-----
======================================================================

[+] Private Key:
======================================================================
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC+Ct8fYnzQ7mPh
vN3J8HkGjKwX4pQqFmYzB2hN5xE9WLqP0KsJ9m3RdTvX8l2QhNpWzYuT6H5pL8...
-----END PRIVATE KEY-----
======================================================================

[WARNING] Store the private key securely! It will be needed later.

[+] Certificate and Private Key saved to: csr_certificates/certificate_and_key_20260312_143025.txt
[WARNING] Keep this file secure and delete it after use!
[LOG] Saved to: logs/certificate_csr_20260312_143025.json

[SUCCESS] Certificate Signing Request generated successfully!
[+] The CSR and private key have been saved to the csr_certificates/ directory
[+] Submit the CSR to your Certificate Authority to obtain a signed certificate
```

**Archivos generados:**
1. `csr_certificates/certificate_and_key_20260312_143025.txt` - CSR y clave privada
2. `logs/certificate_csr_20260312_143025.json` - Metadatos de la operación

**Contenido del log JSON:**
```json
{
  "subject_name": "C=ES,ST=Madrid,L=Madrid,CN=nas01.company.com",
  "algorithm": "RSA",
  "key_size": 2048,
  "hash_function": "SHA256",
  "request_time": "2026-03-12 14:30:25",
  "signing_request": "-----BEGIN CERTIFICATE REQUEST-----\nMIICwjCCAaoCAQ...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBg..."
}
```

**Siguiente paso:**  
Envía el CSR (contenido de `certificate_and_key_*.txt`) a tu Certificate Authority (CA). La CA verificará tu identidad y te devolverá un certificado firmado.

---

### Opción 2: Instalar Certificado Firmado

**Pre-requisitos:**
1. Certificado público firmado por CA (archivo `.crt` o `.pem`)
2. Clave privada generada con el CSR (archivo `.key` o `.pem`)
3. Ambos archivos en formato PEM

**Workflow completo:**

```
Select an option: 2

[*] Starting certificate installation workflow...
======================================================================
[+] Config.yaml loader: config.yaml
[+] Configuration loaded successfully
[+] Target cluster: cluster1.demo.netapp.com
[+] SVM to create: svm_production_01

[*] Establishing connection to cluster: cluster1.demo.netapp.com
[+] Connection successful!
[+] Cluster name: cluster1
[+] ONTAP version: NetApp Release 9.15.1

======================================================================
 PASO 1: VALIDAR PARÁMETROS DE CONFIGURACIÓN
======================================================================

[+] Certificate name: production_cert_2026
[+] Certificate type: server
[+] Public certificate file: certificates/server_cert.crt
[+] Private key file: certificates/private_key.key
[+] SVM name: svm_production_01

======================================================================
 PASO 2: LEER ARCHIVOS DE CERTIFICADO
======================================================================

[+] Reading public certificate from: certificates/server_cert.crt
[+] Public certificate loaded successfully (1456 characters)

[+] Reading private key from: certificates/private_key.key
[+] Private key loaded successfully (1704 characters)

======================================================================
 PASO 3: INSTALAR CERTIFICADO EN ONTAP
======================================================================

[*] Installing certificate via CLI API...
[*] Command: security certificate install -vserver svm_production_01 -type server

[+] Certificate installation successful!
[+] Certificate UUID: 4ff70002-13e1-11f1-a019-d039eaccfdc5

======================================================================
 PASO 4: VERIFICAR INSTALACIÓN
======================================================================

[+] Certificate installed and verified:
    - Name: production_cert_2026
    - Type: server
    - Common Name: nas01.company.com
    - CA: vdc-ca
    - Serial Number: 7BB05FC50001000001E2
    - Expiry: 2028-02-24T17:32:32+01:00

[LOG] Saved to: logs/certificate_install_20260312_144103.json

[SUCCESS] Certificate installation process completed!
[+] The certificate is now installed on SVM: svm_production_01
```

**Contenido del log JSON:**
```json
{
  "operation": "certificate_install",
  "svm_name": "svm_production_01",
  "cert_name": "production_cert_2026",
  "cert_type": "server",
  "common_name": "nas01.company.com",
  "ca": "vdc-ca",
  "serial_number": "7BB05FC50001000001E2",
  "expiry_time": "2028-02-24T17:32:32+01:00",
  "uuid": "4ff70002-13e1-11f1-a019-d039eaccfdc5",
  "timestamp": "2026-03-12 14:41:03",
  "status": "success"
}
```

**Siguiente paso:**  
El certificado está instalado pero aún no está en uso. Usa la Opción 3 para configurar SSL y activar el certificado.

---

### Opción 3: Modificar SSL y Eliminar Certificado Antiguo

**Descripción:**  
Workflow combinado en 2 pasos:
1. Modifica la configuración SSL para usar el certificado instalado
2. Elimina el certificado autofirmado antiguo (CA = nombre SVM)

**Workflow completo:**

```
Select an option: 3

======================================================================
[*] SSL Modification & Certificate Cleanup - SVM: svm_production_01
======================================================================

[+] Config.yaml loader: config.yaml
[+] Configuration loaded successfully
[+] Target cluster: cluster1.demo.netapp.com
[+] SVM to create: svm_production_01

[*] Establishing connection to cluster: cluster1.demo.netapp.com
[+] Connection successful!
[+] Cluster name: cluster1
[+] ONTAP version: NetApp Release 9.15.1

[*] Getting serial numbers for SVM: svm_production_01

[+] Found 2 certificates in SVM svm_production_01:

╔════════════════════════════════════════════════════════════════════╗
║  Certificate Name          Serial Number        CA                 ║
╠════════════════════════════════════════════════════════════════════╣
║  production_cert_2026      7BB05FC50001000001E2  vdc-ca            ║
║  svm_production_01_1897... 189723A159E02619      svm_production_01 ║
╚════════════════════════════════════════════════════════════════════╝

[LOG] Saved to: logs/serial_numbers_20260312_145942.json

======================================================================
[STEP 1/2] Modifying SSL configuration...
======================================================================

[*] Using certificate:
    Name: production_cert_2026
    CA: vdc-ca
    CN: nas01.company.com
    Serial: 7BB05FC50001000001E2

======================================================================
[*] SSL Modification - VServer: svm_production_01
======================================================================

[+] SSL Configuration parameters:
    - VServer: svm_production_01
    - Server Enabled: true
    - CA Name: vdc-ca
    - Common Name: nas01.company.com
    - Serial Number: 7BB05FC50001000001E2

[*] Executing SSL modification via CLI API...
[*] Command: security ssl modify -vserver svm_production_01 -server-enabled true

[+] SSL configuration modified successfully!

[*] Verifying SSL configuration...
[+] SSL verification successful!
[+] Current SSL configuration:
    - VServer: svm_production_01
    - Server Enabled: true
    - CA: vdc-ca
    - Common Name: nas01.company.com
    - Serial: 7BB05FC50001000001E2

[LOG] Saved to: logs/ssl_modify_20260312_145943.json
[LOG] Saved to: logs/security_ssl_show_20260312_145944.json

======================================================================
[STEP 2/2] Deleting old certificate...
======================================================================

[*] Old certificate to delete:
    Name: svm_production_01_189723A159E02619
    CA: svm_production_01
    Serial: 189723A159E02619

[*] Searching for certificate with serial: 189723A159E02619
[+] Certificate found: svm_production_01_189723A159E02619
[+] UUID: 7d81e8d8-1160-11f1-9388-d039eaccfd99

[*] Deleting certificate...
[+] Certificate deleted successfully!

[*] Verifying deletion...
[+] Certificate no longer exists - Deletion confirmed

[LOG] Saved to: logs/certificate_delete_20260312_145945.json

======================================================================
  PROCESS COMPLETED SUCCESSFULLY
======================================================================

[✓] SSL configuration updated with certificate: production_cert_2026
[✓] Old certificate deleted: svm_production_01_189723A159E02619
```

**Archivos generados:**
1. `logs/serial_numbers_20260312_145942.json` - Lista de certificados consultados
2. `logs/ssl_modify_20260312_145943.json` - Resultado de modificación SSL
3. `logs/security_ssl_show_20260312_145944.json` - Verificación SSL
4. `logs/certificate_delete_20260312_145945.json` - Confirmación de eliminación

---

### Opción 0: Salir con Backup de Event Logs

```
Select an option: 0

[*] Exiting script...

[*] Creating backup of event logs...
[*] Fetching event logs from cluster...
[+] Retrieved 100 event logs
[LOG] Saved to: logs/event_logs_20260312_150000.json

[+] Script execution completed successfully
[+] Event logs backup saved for auditing
```

---

### Opción 9: Salir sin Event Logs

```
Select an option: 9

[*] Exiting without event logs backup...
[+] Script terminated
```

---

### Workflow Completo: Renovación de Certificado

**Escenario:** Renovar certificado que expira pronto.

**Paso 1 - Generar nuevo CSR (Opción 1):**
```bash
# Ejecutar script
python ca_certificates.py
# Seleccionar opción 1
# CSR guardado en: csr_certificates/certificate_and_key_20260312_143025.txt
```

**Paso 2 - Enviar CSR a CA:**
```bash
# Copiar el contenido del CSR desde el archivo generado
# Enviarlo a tu Certificate Authority (proceso externo al script)
# Recibir certificado firmado: server_cert.crt
```

**Paso 3 - Actualizar config.yaml:**
```yaml
certificate:
  cert_name: production_cert_2026
  type: server
  public_certificate_file: server_cert.crt
  private_key_file: csr_certificates/certificate_and_key_20260312_143025.txt
ssl:
  server_enabled: true
```

**Paso 4 - Instalar certificado (Opción 2):**
```bash
python ca_certificates.py
# Seleccionar opción 2
# Certificado instalado exitosamente
```

**Paso 5 - Activar SSL y limpiar (Opción 3):**
```bash
python ca_certificates.py
# Seleccionar opción 3
# SSL actualizado + certificado antiguo eliminado
```

**Paso 6 - Verificación:**
```bash
# En ONTAP CLI:
vserver services web show -vserver svm_production_01
security ssl show -vserver svm_production_01
security certificate show -vserver svm_production_01
```

## Registro de Errores

### Errores de Configuración

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| FileNotFoundError | `config.yaml not found` | Archivo config.yaml no existe en el directorio | Crear archivo config.yaml siguiendo la guía |
| yaml.YAMLError | `Invalid YAML format` | Sintaxis YAML incorrecta (indentación, caracteres especiales) | Validar YAML con linter online o IDE |
| KeyError | `Missing required fields` | Falta sección cluster, svm o certificate | Agregar secciones requeridas a config.yaml |
| ValidationError | `Incomplete configuration` | Sección existe pero falta campos (host, username, password, name) | Completar todos los campos requeridos |
| PermissionError | `Insufficient permissions to read` | Sin permisos de lectura del archivo | `chmod 644 config.yaml` o verificar permisos |

**Ejemplo de error:**
```
[ERROR] File not found: config.yaml
[ERROR] Please check the path and try again
```

---

### Errores de Conexión

| Código HTTP | Descripción | Causa | Solución |
|-------------|-------------|-------|----------|
| 401 | Authentication failed | Usuario o contraseña incorrectos | Verificar credenciales en config.yaml |
| 403 | Forbidden | Usuario sin permisos de seguridad | Usar cuenta `admin` o con rol `security` |
| 404 | Resource not found | Cluster o SVM no existen / URL incorrecta | Verificar hostname/IP del cluster |
| ConnectionError | Cannot reach host | Host no accesible por red / firewall bloqueando | Verificar conectividad: `ping <host>` |
| TimeoutError | Connection timeout | Cluster no responde en tiempo razonable | Verificar estado del cluster |
| SSLError | SSL verification failed | Certificado SSL del cluster inválido (si verify=True) | Usar `verify=False` o instalar certificado CA |

**Ejemplo de error 401:**
```
[ERROR] NetApp REST API error
[ERROR] HTTP status: 401
[ERROR] Authentication failed
[ERROR] Invalid username or password for user 'admin'
```

**Ejemplo de error de conexión:**
```
[ERROR] Cannot reach host '10.0.0.100'
[ERROR] Check network connectivity and hostname/IP
```

---

### Errores de Generación de CSR

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| 400 | Bad request - Invalid parameters | Parámetros de certificado inválidos | Verificar size, algorithm, hash_function |
| 403 | Forbidden | Sin permisos `security certificate create` | Usar cuenta con permisos adecuados |
| ValidationError | `Missing required fields` | Falta common_name, size, algorithm, hash_function, country, state o locality | Completar todos los campos requeridos en sección certificate |
| ValueError | Invalid size | size no es 2048, 3072, 4096 o 7680 | Usar valores válidos de tamaño de clave |
| ValueError | Invalid algorithm | algorithm no es RSA o EC | Usar 'RSA' o 'EC' |
| ValueError | Invalid hash_function | hash_function no es SHA256, SHA384 o SHA512 | Usar función hash válida |

**Ejemplo de error:**
```
[ERROR] NetApp API error during CSR generation
[ERROR] HTTP Status: 400
[ERROR] Bad request - Check certificate parameters
[ERROR] Details: Invalid key size specified
```

**Campo faltante:**
```
[ERROR] Missing required fields in certificate config: country, state, locality
```

---

### Errores de Instalación de Certificados

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| FileNotFoundError | Certificate file not found | Archivo public_certificate_file no existe | Verificar ruta del archivo |
| FileNotFoundError | Private key file not found | Archivo private_key_file no existe | Verificar ruta del archivo |
| 409 | Conflict - Certificate exists | Ya existe certificado con ese cert_name | Cambiar cert_name o eliminar certificado existente |
| 422 | Unprocessable entity | Certificado y clave privada no coinciden / Formato PEM inválido | Verificar que certificado y clave corresponden al mismo CSR |
| ValidationError | Invalid certificate format | Certificado no está en formato PEM | Asegurar que certificado tiene `-----BEGIN CERTIFICATE-----` |
| ValidationError | Invalid private key format | Clave privada no está en formato PEM | Asegurar que clave tiene `-----BEGIN PRIVATE KEY-----` |
| ValidationError | Missing cert_name | cert_name no definido en config.yaml | Agregar campo cert_name |
| ValidationError | Missing type | type no definido | Agregar campo type (server, client, etc.) |

**Ejemplo de error 404:**
```
[ERROR] File not found: certificates/server_cert.crt
[ERROR] Please check the path: certificates/server_cert.crt
[ERROR] Current directory: C:\Users\admin\certificates\
```

**Ejemplo de error 422:**
```
[ERROR] NetApp API error during certificate installation
[ERROR] HTTP Status: 422
[ERROR] Details: Certificate and private key do not match
[ERROR] Verify that both files correspond to the same CSR
```

**Ejemplo de conflicto 409:**
```
[ERROR] Certificate installation failed
[ERROR] HTTP Status: 409
[ERROR] Conflict: Certificate with name 'production_cert_2026' already exists
[ERROR] SOLUTION: Choose a different cert_name or delete the existing certificate
```

---

### Errores de Modificación SSL

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| 400 | Bad request | Parámetros SSL inválidos (server_enabled no es bool) | Usar `true` o `false` para server_enabled |
| 404 | Certificate not found | Serial number no corresponde a ningún certificado | Verificar serial numbers con get_serial_numbers() |
| ValidationError | Missing server_enabled | ssl.server_enabled no definido en config.yaml | Agregar campo server_enabled en sección ssl |
| ValueError | Invalid CA name | No se puede extraer CA name del certificado | Proporcionar ca_name manualmente |
| NetAppRestError | SSL modify failed | Comando CLI falló por configuración conflictiva | Revisar configuración SSL actual: `security ssl show` |

**Ejemplo de error:**
```
[ERROR] NetApp API error during SSL modification
[ERROR] HTTP Status: 404
[ERROR] Certificate not found with serial: 7BB05FC50001000001E2
[ERROR] Run get_serial_numbers() to see available certificates
```

**Campo faltante:**
```
[ERROR] Missing 'server_enabled' in config.yaml
[ERROR] Add 'ssl:' section with 'server_enabled: true' or 'server_enabled: false'
```

---

### Errores de Eliminación de Certificados

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| 404 | Certificate not found | Certificado ya eliminado o serial incorrecto | Verificar certificados existentes con get_serial_numbers() |
| 409 | Conflict - Certificate in use | Certificado está asignado a la configuración SSL | Modificar SSL para usar otro certificado primero (Opción 3 Step 1) |
| ValidationError | Missing serial_number | serial_number no proporcionado | Proporcionar serial_number válido |
| NetAppRestError | Delete failed | Error genérico de API | Verificar logs de ONTAP: `security certificate show` |

**Ejemplo de error 409:**
```
[ERROR] NetApp API error during certificate deletion
[ERROR] HTTP Status: 409
[ERROR] Conflict: Certificate is currently in use by SSL configuration
[ERROR] SOLUTION: Modify SSL to use different certificate before deleting
```

**Ejemplo de certificado no encontrado:**
```
[ERROR] Certificate not found with serial: 189723A159E02619
[ERROR] Certificate may have been already deleted
[ERROR] Verify certificates with: get_serial_numbers()
```

---

### Errores de Consulta de Serial Numbers

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| 404 | SVM not found | Nombre de SVM incorrecto | Verificar nombre exacto de SVM: `vserver show` |
| 403 | Forbidden | Sin permisos para consultar certificados | Usar cuenta con permisos `security certificate show` |
| NetAppRestError | API query failed | Error de API REST | Verificar conectividad y permisos |

**Ejemplo de error:**
```
[ERROR] Could not retrieve serial numbers for SVM: svm_nonexistent
[ERROR] HTTP Status: 404
[ERROR] SVM not found - Check SVM name in config.yaml
```

---

### Errores de Event Logs

| Código | Descripción | Causa | Solución |
|--------|-------------|-------|----------|
| 403 | Forbidden | Sin permisos para event logs | Usar cuenta admin con permisos `event log show` |
| NetAppRestError | EMS query failed | Error al consultar EMS | Verificar que cluster esté funcional |

**Ejemplo de error:**
```
[WARNING] Failed to retrieve event logs
[ERROR] HTTP Status: 403
[ERROR] Insufficient permissions for EMS event queries
```

---

### Solución General de Problemas

**Verificaciones básicas:**

1. **Conectividad:**
```bash
ping <cluster_ip>
telnet <cluster_ip> 443
```

2. **Credenciales:**
```bash
# En ONTAP CLI:
security login show -user-or-group-name admin
```

3. **Permisos:**
```bash
# Verificar permisos del usuario
security login role show -role admin
```

4. **Certificados existentes:**
```bash
# En ONTAP CLI:
security certificate show -vserver <svm_name>
```

5. **Configuración SSL actual:**
```bash
security ssl show -vserver <svm_name>
```

6. **Logs de ONTAP:**
```bash
event log show -severity error -time-range "last 1 hour"
```

**Tips de debugging:**
- Revisar archivos en `logs/` para detalles de operaciones
- Activar logs de debug en Python si es necesario
- Verificar formato PEM de certificados: `openssl x509 -in cert.crt -text -noout`
- Verificar clave privada: `openssl rsa -in private.key -check`

## Sistema de Logging

### Características del Sistema

- **Timestamp automático**: Formato `YYYYMMDD_HHMMSS` para ordenación cronológica
- **Formato JSON estructurado**: Fácil parseo con herramientas de análisis
- **Datos reales de ONTAP**: GET después de POST/PATCH para capturar estado actual
- **Directorio dedicado**: `logs/` creado automáticamente si no existe
- **Encoding UTF-8**: Soporte para caracteres especiales y acentos
- **Auditoría completa**: Cada operación genera un log independiente

### Estructura de Directorios

```
CA_certificates/
├── ca_certificates.py
├── config.yaml
├── csr_certificates/              # Archivos generados por Opción 1
│   ├── certificate_and_key_20260312_143025.txt
│   ├── certificate_and_key_20260312_150510.txt
│   └── certificate_csr_20260312_143025.json
└── logs/                          # Logs de operaciones
    ├── certificate_csr_20260312_143025.json
    ├── certificate_install_20260312_144103.json
    ├── serial_numbers_20260312_145942.json
    ├── ssl_modify_20260312_145943.json
    ├── security_ssl_show_20260312_145944.json
    ├── certificate_delete_20260312_145945.json
    └── event_logs_20260312_150000.json
```

---

### Logs Generados por Opción

#### Opción 1: Generate CSR

**1. certificate_csr_YYYYMMDD_HHMMSS.json**

Metadatos del CSR generado.

```json
{
  "subject_name": "C=ES,ST=Madrid,L=Madrid,CN=nas01.company.com",
  "algorithm": "RSA",
  "key_size": 2048,
  "hash_function": "SHA256",
  "request_time": "2026-03-12 14:30:25",
  "signing_request": "-----BEGIN CERTIFICATE REQUEST-----\nMIICwjCCAaoCAQAwfz...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhk..."
}
```

**Campos:**
- `subject_name`: Distinguished Name completo del certificado
- `algorithm`: Algoritmo de cifrado usado (RSA, EC)
- `key_size`: Tamaño de la clave en bits
- `hash_function`: Función hash para firma
- `request_time`: Timestamp de generación
- `signing_request`: CSR completo en formato PEM
- `private_key`: Clave privada generada en formato PEM

---

#### Opción 2: Install Certificate

**2. certificate_install_YYYYMMDD_HHMMSS.json**

Confirmación de instalación con datos del certificado instalado.

```json
{
  "operation": "certificate_install",
  "svm_name": "svm_production_01",
  "cert_name": "production_cert_2026",
  "cert_type": "server",
  "common_name": "nas01.company.com",
  "ca": "vdc-ca",
  "serial_number": "7BB05FC50001000001E2",
  "expiry_time": "2028-02-24T17:32:32+01:00",
  "uuid": "4ff70002-13e1-11f1-a019-d039eaccfdc5",
  "timestamp": "2026-03-12 14:41:03",
  "status": "success"
}
```

**Campos:**
- `operation`: Tipo de operación realizada
- `svm_name`: SVM donde se instaló
- `cert_name`: Nombre del certificado en ONTAP
- `cert_type`: Tipo de certificado (server, client, etc.)
- `common_name`: CN del certificado
- `ca`: Autoridad Certificadora que firmó el certificado
- `serial_number`: Serial number único del certificado
- `expiry_time`: Fecha de expiración en formato ISO 8601
- `uuid`: UUID del certificado en ONTAP
- `timestamp`: Momento de la operación
- `status`: Estado de la operación (success, failed)

---

#### Opción 3: Modify SSL and Delete Certificate

**3. serial_numbers_YYYYMMDD_HHMMSS.json**

Lista de todos los certificados consultados antes del workflow.

```json
{
  "operation": "get_serial_numbers",
  "svm_name": "svm_production_01",
  "total_certificates": 2,
  "total_serial_numbers": 2,
  "serial_numbers": [
    "7BB05FC50001000001E2",
    "189723A159E02619"
  ],
  "certificate_details": [
    {
      "certificate_name": "production_cert_2026",
      "common_name": "nas01.company.com",
      "serial_number": "7BB05FC50001000001E2",
      "type": "server",
      "ca": "vdc-ca",
      "expiry_time": "2028-02-24T17:32:32+01:00",
      "uuid": "4ff70002-13e1-11f1-a019-d039eaccfdc5"
    },
    {
      "certificate_name": "svm_production_01_189723A159E02619",
      "common_name": "svm_production_01",
      "serial_number": "189723A159E02619",
      "type": "server",
      "ca": "svm_production_01",
      "expiry_time": "2027-02-24T10:09:14+01:00",
      "uuid": "7d81e8d8-1160-11f1-9388-d039eaccfd99"
    }
  ],
  "timestamp": "2026-03-12 14:59:42"
}
```

**4. ssl_modify_YYYYMMDD_HHMMSS.json**

Resultado de la modificación SSL (Step 1).

```json
{
  "operation": "ssl_modify",
  "svm_name": "svm_production_01",
  "server_enabled": true,
  "ca_name": "vdc-ca",
  "common_name": "nas01.company.com",
  "serial_number": "7BB05FC50001000001E2",
  "timestamp": "2026-03-12 14:59:43",
  "status": "success"
}
```

**5. security_ssl_show_YYYYMMDD_HHMMSS.json**

Verificación de configuración SSL después de modificación.

```json
{
  "operation": "security_ssl_show",
  "svm_name": "svm_production_01",
  "ssl_configuration": {
    "vserver": "svm_production_01",
    "server_enabled": "true",
    "ca": "vdc-ca",
    "common_name": "nas01.company.com",
    "serial": "7BB05FC50001000001E2",
    "client_enabled": "false"
  },
  "timestamp": "2026-03-12 14:59:44"
}
```

**6. certificate_delete_YYYYMMDD_HHMMSS.json**

Confirmación de eliminación de certificado (Step 2).

```json
{
  "operation": "certificate_delete",
  "svm_name": "svm_production_01",
  "serial_number": "189723A159E02619",
  "certificate_name": "svm_production_01_189723A159E02619",
  "common_name": "svm_production_01",
  "ca_name": "svm_production_01",
  "type": "server",
  "uuid": "7d81e8d8-1160-11f1-9388-d039eaccfd99",
  "timestamp": "2026-03-12 14:59:45",
  "status": "deleted"
}
```

---

#### Opción 0: Exit with Event Logs

**7. event_logs_YYYYMMDD_HHMMSS.json**

Backup de event logs del cluster para auditoría.

```json
{
  "operation": "event_logs_backup",
  "cluster_name": "cluster1",
  "total_events": 100,
  "timestamp": "2026-03-12 15:00:00",
  "events": [
    {
      "index": 1,
      "time": "2026-03-12T14:59:45+01:00",
      "node": "cluster1-01",
      "severity": "INFORMATIONAL",
      "event": "security.certificate.delete",
      "message": "Certificate with serial number 189723A159E02619 deleted from vserver svm_production_01"
    },
    {
      "index": 2,
      "time": "2026-03-12T14:59:43+01:00",
      "node": "cluster1-01",
      "severity": "INFORMATIONAL",
      "event": "security.ssl.modify",
      "message": "SSL configuration modified for vserver svm_production_01"
    },
    {
      "index": 3,
      "time": "2026-03-12T14:41:03+01:00",
      "node": "cluster1-01",
      "severity": "INFORMATIONAL",
      "event": "security.certificate.install",
      "message": "Certificate production_cert_2026 installed in vserver svm_production_01"
    }
  ]
}
```

---

### Uso de Logs para Auditoría

#### Consultar Operaciones por Fecha

```bash
# Listar logs de un día específico
ls logs/*20260312*.json

# Ver logs de instalación
cat logs/certificate_install_20260312_*.json | jq .

# Ver todos los serial numbers consultados
cat logs/serial_numbers_*.json | jq '.serial_numbers'
```

#### Verificar Estado de Certificados

```bash
# Último certificado instalado
cat logs/certificate_install_*.json | tail -1 | jq '.cert_name, .expiry_time'

# Certificados eliminados
cat logs/certificate_delete_*.json | jq '.certificate_name, .timestamp'
```

#### Análisis de Event Logs

```bash
# Eventos relacionados con certificados
cat logs/event_logs_*.json | jq '.events[] | select(.event | contains("certificate"))'

# Eventos de seguridad por severidad
cat logs/event_logs_*.json | jq '.events[] | select(.severity == "ERROR")'
```

---

### Retención y Limpieza

**Recomendaciones:**

1. **Retención de logs:** 90 días para auditoría de seguridad
2. **Backup:** Copiar directorio `logs/` periódicamente
3. **Limpieza:** Script para eliminar logs antiguos

```bash
# Eliminar logs de más de 90 días (PowerShell)
Get-ChildItem logs\*.json | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-90)} | Remove-Item

# Eliminar logs de más de 90 días (Bash)
find logs/ -name "*.json" -type f -mtime +90 -delete
```

4. **Compresión:** Comprimir logs antiguos para ahorrar espacio

```bash
# Comprimir logs del año anterior
tar -czf logs_2025.tar.gz logs/*2025*.json
```

---

### Integración con SIEM

Los logs JSON pueden integrarse con sistemas SIEM (Security Information and Event Management):

**Ejemplo con Splunk:**
```bash
# Configurar Splunk Universal Forwarder
[monitor://C:\path\to\CA_certificates\logs\]
sourcetype = json
index = netapp_security
```

**Ejemplo con Elasticsearch:**
```bash
# Ingestar logs con Logstash
input {
  file {
    path => "C:/path/to/CA_certificates/logs/*.json"
    codec => "json"
  }
}
```

**Ejemplo con Azure Monitor:**
```powershell
# Enviar logs a Azure Log Analytics
$logs = Get-Content logs\certificate_install_*.json | ConvertFrom-Json
foreach ($log in $logs) {
    Send-AzOperationalInsightsData -WorkspaceId $workspaceId -LogType "NetAppCertificates" -JsonPayload $log
}
```

## Seguridad y Buenas Prácticas

### Gestión de Credenciales

**CRÍTICO - NO comprometer credenciales:**

1. **NO subir config.yaml a repositorios públicos**
   ```bash
   # Agregar a .gitignore
   echo "config.yaml" >> .gitignore
   echo "*.key" >> .gitignore
   echo "*.pem" >> .gitignore
   echo "csr_certificates/*.txt" >> .gitignore
   ```

2. **Usar variables de entorno en producción**
   ```python
   # Modificar ca_certificates.py para usar:
   import os
   cluster_config = {
       'host': os.getenv('ONTAP_HOST'),
       'username': os.getenv('ONTAP_USER'),
       'password': os.getenv('ONTAP_PASSWORD')
   }
   ```
   
   ```bash
   # En PowerShell:
   $env:ONTAP_HOST = "cluster1.company.com"
   $env:ONTAP_USER = "admin"
   $env:ONTAP_PASSWORD = "SecurePassword123"
   
   # En Bash:
   export ONTAP_HOST="cluster1.company.com"
   export ONTAP_USER="admin"
   export ONTAP_PASSWORD="SecurePassword123"
   ```

3. **Gestores de secretos empresariales**
   - **Azure Key Vault**: Para entornos Azure
   - **HashiCorp Vault**: Gestión centralizada de secretos
   - **AWS Secrets Manager**: Para AWS
   - **CyberArk**: Enterprise secrets management
   
   ```python
   # Ejemplo con Azure Key Vault
   from azure.keyvault.secrets import SecretClient
   from azure.identity import DefaultAzureCredential
   
   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)
   
   password = client.get_secret("ontap-admin-password").value
   ```

4. **Permisos restrictivos del archivo config.yaml**
   ```bash
   # Linux/macOS
   chmod 600 config.yaml
   chown admin:admin config.yaml
   
   # PowerShell (Windows)
   icacls config.yaml /inheritance:r /grant:r "$env:USERNAME:RW"
   ```

---

### Gestión de Claves Privadas

**La clave privada es el activo MÁS CRÍTICO del workflow de certificados.**

#### Protección de Claves Privadas

1. **Permisos de archivo estrictos**
   ```bash
   # Linux/macOS
   chmod 600 private_key.key
   chmod 700 csr_certificates/
   
   # PowerShell (Windows)
   icacls private_key.key /inheritance:r /grant:r "$env:USERNAME:R"
   ```

2. **Cifrado en reposo**
   ```bash
   # Cifrar clave privada con AES-256
   openssl enc -aes-256-cbc -salt -in private.key -out private.key.enc
   
   # Descifrar cuando se necesite
   openssl enc -aes-256-cbc -d -in private.key.enc -out private.key
   ```

3. **Almacenamiento seguro**
   - **NO** enviar por email
   - **NO** compartir por chat/mensajería
   - **NO** almacenar en repositorios git
   - Usar USB cifrado para transferencias físicas
   - Almacenar en HSM (Hardware Security Module) para producción

4. **Limpieza después de uso**
   ```bash
   # Eliminar claves privadas después de instalar certificado
   shred -u -z -n 5 private_key.key  # Linux (sobrescribe 5 veces)
   
   # PowerShell (Windows)
   $file = "private_key.key"
   $bytes = [System.IO.File]::ReadAllBytes($file)
   for ($i=0; $i -lt $bytes.Count; $i++) { $bytes[$i] = 0 }
   [System.IO.File]::WriteAllBytes($file, $bytes)
   Remove-Item $file -Force
   ```

5. **Backup cifrado**
   ```bash
   # Crear backup cifrado de directorio csr_certificates/
   tar -czf - csr_certificates/ | openssl enc -aes-256-cbc -out backup_certs.tar.gz.enc
   
   # Restaurar
   openssl enc -aes-256-cbc -d -in backup_certs.tar.gz.enc | tar -xzf -
   ```

#### Rotación de Claves

**Política recomendada:**
- **Certificados de producción**: Renovar cada 1-2 años
- **Certificados internos**: Renovar cada 3-5 años (según política)
- **Ante compromiso**: Renovación inmediata

**Proceso de rotación:**
1. Generar nuevo CSR (Opción 1)
2. Obtener certificado firmado de CA
3. Instalar nuevo certificado (Opción 2)
4. Actualizar SSL y eliminar certificado antiguo (Opción 3)
5. Eliminar claves privadas del certificado antiguo

---

### Gestión de Certificados

#### Selección de Parámetros

**Tamaño de clave:**
| Tamaño | Seguridad | Performance | Compatibilidad | Recomendación |
|--------|-----------|-------------|----------------|---------------|
| 2048 bits | ✓ Buena | ✓✓✓ Excelente | ✓✓✓ Universal | **Recomendado para mayoría de casos** |
| 3072 bits | ✓✓ Muy buena | ✓✓ Buena | ✓✓ Alta | Entornos de alta seguridad |
| 4096 bits | ✓✓✓ Excelente | ✓ Aceptable | ✓✓ Alta | Certificados CA raíz, datos extremadamente sensibles |
| 7680 bits | ✓✓✓ Máxima | ⚠️ Lenta | ⚠️ Limitada | Casos muy especiales (rara vez necesario) |

**Función hash:**
| Hash | Seguridad | Performance | Recomendación |
|------|-----------|-------------|---------------|
| SHA256 | ✓✓ Muy buena | ✓✓✓ Rápida | **Recomendado - Balance ideal** |
| SHA384 | ✓✓✓ Excelente | ✓✓ Buena | Entornos de alta seguridad |
| SHA512 | ✓✓✓ Máxima | ✓ Aceptable | Requisitos regulatorios específicos |

**Algoritmo:**
- **RSA**: Estándar de la industria, compatibilidad universal
- **EC (Elliptic Curve)**: Más eficiente, claves más pequeñas, menor adopción

#### Monitoreo de Expiración

**Alertas proactivas:**

```bash
# Script para verificar certificados próximos a expirar (bash)
#!/bin/bash
THRESHOLD_DAYS=30
for cert in $(ls logs/certificate_install_*.json); do
  expiry=$(jq -r '.expiry_time' $cert)
  cert_name=$(jq -r '.cert_name' $cert)
  days_until_expiry=$(( ($(date -d "$expiry" +%s) - $(date +%s)) / 86400 ))
  
  if [ $days_until_expiry -lt $THRESHOLD_DAYS ]; then
    echo "WARNING: Certificate $cert_name expires in $days_until_expiry days ($expiry)"
  fi
done
```

```powershell
# Script para verificar certificados próximos a expirar (PowerShell)
$ThresholdDays = 30
Get-ChildItem logs\certificate_install_*.json | ForEach-Object {
    $log = Get-Content $_ | ConvertFrom-Json
    $expiryDate = [datetime]$log.expiry_time
    $daysUntilExpiry = ($expiryDate - (Get-Date)).Days
    
    if ($daysUntilExpiry -lt $ThresholdDays) {
        Write-Warning "Certificate $($log.cert_name) expires in $daysUntilExpiry days ($expiryDate)"
    }
}
```

**Calendario de renovación:**
1. **90 días antes**: Iniciar proceso de renovación
2. **60 días antes**: CSR generado y enviado a CA
3. **30 días antes**: Certificado instalado en paralelo
4. **7 días antes**: Migración a nuevo certificado
5. **Día de expiración**: Certificado antiguo eliminado

#### Validación de Certificados

**Antes de instalar:**

```bash
# Verificar formato PEM del certificado
openssl x509 -in server_cert.crt -text -noout

# Verificar clave privada
openssl rsa -in private_key.key -check

# Verificar que certificado y clave coinciden
cert_modulus=$(openssl x509 -noout -modulus -in server_cert.crt | openssl md5)
key_modulus=$(openssl rsa -noout -modulus -in private_key.key | openssl md5)

if [ "$cert_modulus" = "$key_modulus" ]; then
    echo "Certificate and key match"
else
    echo "ERROR: Certificate and key do NOT match"
fi
```

**Después de instalar:**

```bash
# En ONTAP CLI
security certificate show -vserver svm_production_01 -cert-name production_cert_2026

# Verificar SSL
security ssl show -vserver svm_production_01

# Probar conectividad SSL
openssl s_client -connect nas01.company.com:443 -servername nas01.company.com
```

---

### Auditoría y Compliance

#### Registro de Operaciones

**Mantener inventario de certificados:**

```yaml
# certificate_inventory.yaml
certificates:
  - name: production_cert_2026
    svm: svm_production_01
    purpose: NAS primary storage
    ca: vdc-ca
    serial: 7BB05FC50001000001E2
    issued: 2026-02-24
    expires: 2028-02-24
    contact: admin@company.com
    last_renewed: 2026-02-24
    next_renewal: 2027-11-24
    
  - name: dr_cert_2026
    svm: svm_dr_01
    purpose: Disaster Recovery NAS
    ca: vdc-ca
    serial: 8CC06GD60002000002F3
    issued: 2026-03-01
    expires: 2028-03-01
    contact: admin@company.com
    last_renewed: 2026-03-01
    next_renewal: 2027-12-01
```

#### Auditoría de Event Logs

**Eventos críticos a monitorear:**

| Evento | Descripción | Acción |
|--------|-------------|--------|
| `security.certificate.install` | Certificado instalado | Verificar autorización |
| `security.certificate.delete` | Certificado eliminado | Verificar justificación |
| `security.ssl.modify` | SSL modificado | Auditar cambios de configuración |
| `security.certificate.expired` | Certificado expirado | Acción inmediata requerida |
| `security.certificate.expiring_soon` | Certificado próximo a expirar | Programar renovación |

**Consulta de event logs:**

```bash
# En ONTAP CLI
event log show -event security.certificate.* -time-range "last 7 days"

# Filtrar por severidad
event log show -severity error,alert -event security.* -time-range "last 30 days"
```

#### Compliance y Regulaciones

**Estándares aplicables:**
- **PCI-DSS**: Requisitos para certificados en sistemas de pago
- **HIPAA**: Certificados para datos de salud
- **SOC 2**: Gestión de certificados en auditorías
- **ISO 27001**: Gestión de activos criptográficos
- **NIST**: Estándares de criptografía (FIPS 140-2)

**Requisitos comunes:**
- Tamaño mínimo de clave: 2048 bits (muchas regulaciones)
- Hash mínimo: SHA-256 (deprecación de SHA-1)
- Validación de CA: Uso de CAs reconocidas
- Rotación: Política de renovación documentada
- Auditoría: Logs de todas las operaciones

---

### Validación Pre-Producción

**Checklist antes de implementar en producción:**

- [ ] Certificado generado con parámetros correctos (size >= 2048, SHA256+)
- [ ] CSR enviado a CA autorizada de la empresa
- [ ] Certificado verificado: `openssl x509 -in cert.crt -text -noout`
- [ ] Certificado y clave privada coinciden (verificar modulus)
- [ ] Fechas de validez verificadas (not_before, not_after)
- [ ] Subject Alternative Names incluyen todos los nombres DNS necesarios
- [ ] Certificado instalado en SVM de prueba primero
- [ ] SSL configurado y probado en laboratorio
- [ ] Clientes pueden conectar correctamente
- [ ] Certificado antiguo respaldado antes de eliminar
- [ ] Documentación actualizada (inventario, runbooks)
- [ ] Equipo notificado del cambio
- [ ] Plan de rollback preparado

**Testing en laboratorio:**

```bash
# 1. Verificar desde cliente Linux
openssl s_client -connect nas01.company.com:443 -showcerts

# 2. Verificar desde cliente Windows
certutil -url https://nas01.company.com

# 3. Probar montaje NFS con certificado
mount -t nfs -o sec=sys nas01.company.com:/vol1 /mnt/test

# 4. Probar CIFS
smbclient //nas01.company.com/share -U user

# 5. Verificar cadena de confianza completa
openssl s_client -connect nas01.company.com:443 -CAfile ca_bundle.crt
```

---

### Gestión de Incidentes

#### Compromiso de Clave Privada

**Si se sospecha compromiso de clave privada:**

1. **Revocar certificado inmediatamente** (contactar CA)
2. **Generar nuevo CSR** con nuevas claves (Opción 1)
3. **Obtener certificado de reemplazo** de CA
4. **Instalar nuevo certificado** (Opción 2)
5. **Actualizar SSL** (Opción 3)
6. **Notificar a stakeholders**
7. **Investigar causa del compromiso**
8. **Documentar incidente** en logs de seguridad

#### Certificado Expirado

**Si el certificado expira sin renovación:**

```bash
# Síntomas:
# - Clientes no pueden conectar
# - Errores SSL en logs de ONTAP
# - Alertas de expiración en monitoreo

# Acción inmediata:
# 1. Generar certificado autofirmado temporal (ONTAP CLI)
security certificate create -vserver svm_production_01 -type server -common-name nas01.company.com

# 2. Activar certificado temporal
security ssl modify -vserver svm_production_01 -server-enabled true

# 3. Seguir proceso completo de renovación (Opciones 1-2-3)
```

---

### Mejores Prácticas - Resumen

**DO (Hacer):**
- ✅ Usar claves >= 2048 bits con SHA256+
- ✅ Proteger claves privadas con permisos 600
- ✅ Eliminar claves privadas después de instalar certificados
- ✅ Mantener inventario actualizado de certificados
- ✅ Configurar alertas de expiración (90, 60, 30 días)
- ✅ Probar en laboratorio antes de producción
- ✅ Documentar todos los cambios
- ✅ Usar CA empresarial reconocida
- ✅ Revisar logs/ periódicamente
- ✅ Hacer backup cifrado de certificados activos

**DON'T (No hacer):**
- ❌ NO usar SHA-1 o MD5 (deprecated)
- ❌ NO usar claves < 2048 bits
- ❌ NO compartir claves privadas por email/chat
- ❌ NO subir config.yaml a git
- ❌ NO dejar claves privadas sin cifrar
- ❌ NO usar certificados autofirmados en producción
- ❌ NO ignorar alertas de expiración
- ❌ NO omitir validación de certificados antes de instalar
- ❌ NO eliminar certificados sin verificar que no están en uso
- ❌ NO dejar certificados expirados en el sistema

---

### Recursos Adicionales

**Documentación oficial:**
- [NetApp ONTAP Security Hardening Guide](https://docs.netapp.com/us-en/ontap/security-encryption/)
- [ONTAP REST API Documentation](https://docs.netapp.com/us-en/ontap-automation/)
- [NetApp Security Technical Reports](https://www.netapp.com/media/10674-tr4569.pdf)

**Estándares y compliance:**
- [NIST SP 800-52r2](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf): TLS Guidelines
- [PCI-DSS Requirements](https://www.pcisecuritystandards.org/): Payment Card Industry
- [ISO 27001](https://www.iso.org/isoiec-27001-information-security.html): Information Security Management

**Herramientas:**
- [OpenSSL](https://www.openssl.org/): Validación y gestión de certificados
- [certbot](https://certbot.eff.org/): Automatización Let's Encrypt (CA gratuita)
- [YAML Validator](https://www.yamllint.com/): Validación de config.yaml

---

**Versión del README:** 2.0  
**Última actualización:** Marzo 2026  
**Mantenedor:** NetApp ONTAP Automation Team  
**Contacto:** Revisar documentación interna para soporte
