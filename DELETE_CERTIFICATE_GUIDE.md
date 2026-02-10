# Guía: Delete Certificate - Eliminación de Certificados

## Opción 3 del Menú: Flujo Completo de Gestión de Certificados

### ¿Qué hace esta función?

La **Opción 3** ejecuta un flujo completo de **3 operaciones** en secuencia:

1. **Obtiene serial numbers** de todos los certificados:
   ```bash
   security certificate show -vserver svm_1_cluster -instance
   ```

2. **Modifica la configuración SSL** usando el **segundo serial number**:
   ```bash
   security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial <serial_number_2> -server-enabled true
   ```

3. **Elimina el certificado antiguo** usando el **primer serial number**:
   ```bash
   security certificate delete -type server -vserver svm_1_cluster -ca vdc-ca -serial <serial_number_1> -common-name certificate
   ```

---

## Uso

### 1️⃣ Configuración requerida

En `config.yaml`, asegúrate de tener todos estos parámetros configurados:

```yaml
# SVM Settings
svm:
  name: svm_1_cluster  # Nombre de tu SVM

# SSL Configuration (REQUERIDO)
ssl:
  ca_name: vdc-ca  # Nombre de la CA del certificado
  server_enabled: true  # Habilitar servidor SSL (true/false)

# Certificate Settings
certificate:
  common_name: certificate  # Common name del certificado
  type: server  # Tipo de certificado (server, client, etc.)
  # ... otros parámetros ...
```

### 2️⃣ Prerequisitos

Antes de ejecutar la opción 3, asegúrate de:

1. ✅ Haber generado el CSR (Opción 1)
2. ✅ Haber instalado el certificado firmado (Opción 2)
3. ✅ Tener **al menos 2 certificados** en la SVM

### 3️⃣ Ejecutar la opción 3

1. Ejecuta el script: `python ca_certificates.py`
2. Selecciona la **Opción 3** del menú
3. El script automáticamente ejecuta las 3 operaciones en secuencia

---

## Flujo de ejecución detallado

### Operación 1: Obtención de Serial Numbers

```
======================================================================
  CERTIFICATE SHOW - SVM: svm_1_cluster
======================================================================

Certificate #1:
----------------------------------------------------------------------
Certificate Name: rhoso
Common Name: certificate
Serial Number: 16519C887ED0E2BF91150BC750220DC3A8B720D6  ⭐ (Este se ELIMINARÁ)
Type: server
CA: vdc-ca
...

Certificate #2:
----------------------------------------------------------------------
Certificate Name: svm_1_cluster_1892EAF8B8E7D247
Common Name: certificate
Serial Number: 1892EAF8B8E7D247  ⭐ (Este se usará para SSL)
Type: server
CA: vdc-ca
...

======================================================================
  EXTRACTED SERIAL NUMBERS
======================================================================

[+] Serial Numbers:

    [1] 16519C887ED0E2BF91150BC750220DC3A8B720D6 - Certificate Name: rhoso ⭐
    [2] 1892EAF8B8E7D247 - Certificate Name: svm_1_cluster_1892EAF8B8E7D247 ⭐

======================================================================
```

### Operación 2: Modificación SSL

```
[*] Proceeding with SSL modification using second certificate...
[*] Selected Serial Number: 1892EAF8B8E7D247
[*] Certificate Name: svm_1_cluster_1892EAF8B8E7D247

[STEP 1/3] Validating SSL configuration parameters...
[+] Configuration validated:
    - SVM Name: svm_1_cluster
    - CA Name: vdc-ca
    - Common Name: certificate
    - Serial Number: 1892EAF8B8E7D247
    - Server Enabled: True

[STEP 2/3] Modifying SSL configuration...
[+] SSL Modify Command:
    security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true

[SUCCESS] SSL modification completed successfully!
[+] SSL configuration has been updated
```

### Operación 3: Eliminación del certificado antiguo

```
[*] Proceeding with certificate deletion using first certificate...
[*] Selected Serial Number: 16519C887ED0E2BF91150BC750220DC3A8B720D6
[*] Certificate Name: rhoso

[STEP 1/4] Validating configuration parameters...
[+] Configuration:
    - SVM Name: svm_1_cluster
    - Certificate Type: server
    - CA Name: vdc-ca
    - Common Name: certificate
    - Serial Number: 16519C887ED0E2BF91150BC750220DC3A8B720D6

[STEP 2/4] Locating certificate...
[+] Certificate found:
    - UUID: 12345678-1234-1234-1234-123456789012
    - Name: rhoso
    - Common Name: certificate
    - Type: server
    - Serial Number: 16519C887ED0E2BF91150BC750220DC3A8B720D6

[STEP 3/4] Deleting certificate...
[+] CLI Command:
    security certificate delete -type server -vserver svm_1_cluster -ca vdc-ca -serial 16519C887ED0E2BF91150BC750220DC3A8B720D6 -common-name certificate

[*] Executing certificate deletion...
[+] Certificate deleted successfully!

[STEP 4/4] Verification...
[+] Certificate successfully removed from the system

======================================================================
  REMAINING CERTIFICATES - SVM: svm_1_cluster
======================================================================

[1] Certificate:
    Name: svm_1_cluster_1892EAF8B8E7D247
    Common Name: certificate
    Serial Number: 1892EAF8B8E7D247
    Type: server

======================================================================
[INFO] Total remaining certificates: 1

[SUCCESS] Certificate deletion completed successfully!
```

### Resumen final

```
======================================================================
  WORKFLOW COMPLETED SUCCESSFULLY
======================================================================

[✓] Serial numbers retrieved
[✓] SSL configuration modified
[✓] Old certificate deleted

[INFO] All operations completed successfully!
```

---

## Parámetros del comando Certificate Delete

| Parámetro | Fuente en config.yaml | Ejemplo | Descripción |
|-----------|----------------------|---------|-------------|
| `-type` | `certificate.type` | `server` | Tipo de certificado |
| `-vserver` | `svm.name` | `svm_1_cluster` | Nombre de la SVM |
| `-ca` | `ssl.ca_name` | `vdc-ca` | Nombre de la CA |
| `-serial` | Primer serial number del show | `16519C887ED0E2BF91150BC750220DC3A8B720D6` | Serial number del certificado |
| `-common-name` | `certificate.common_name` | `certificate` | Common Name del certificado |

---

## Archivos de log generados

### 1. `logs/serial_numbers_*.json`

Contiene todos los serial numbers encontrados.

### 2. `logs/ssl_modify_*.json`

```json
{
  "operation": "ssl_modify",
  "svm_name": "svm_1_cluster",
  "ca_name": "vdc-ca",
  "common_name": "certificate",
  "serial_number": "1892EAF8B8E7D247",
  "server_enabled": true,
  "cli_command": "security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true",
  "timestamp": "2026-02-10 15:30:25"
}
```

### 3. `logs/certificate_delete_*.json`

```json
{
  "operation": "certificate_delete",
  "svm_name": "svm_1_cluster",
  "serial_number": "16519C887ED0E2BF91150BC750220DC3A8B720D6",
  "cert_type": "server",
  "ca_name": "vdc-ca",
  "common_name": "certificate",
  "cli_command": "security certificate delete -type server -vserver svm_1_cluster -ca vdc-ca -serial 16519C887ED0E2BF91150BC750220DC3A8B720D6 -common-name certificate",
  "timestamp": "2026-02-10 15:30:30"
}
```

---

## Lógica de selección de certificados

### ¿Por qué estos serial numbers?

**Orden de las operaciones:**

1. **Primer certificado** (índice [1] en el show):
   - Es el certificado **antiguo** que se va a **eliminar**
   - Normalmente es el certificado que estaba instalado anteriormente
   - Se elimina después de configurar SSL con el nuevo

2. **Segundo certificado** (índice [2] en el show):
   - Es el **nuevo certificado** que acabas de instalar (Opción 2)
   - Se usa para **configurar SSL**
   - Este permanecerá activo en la SVM

**Flujo típico:**
```
ANTES:
  [1] Certificado antiguo (rhoso)
  [2] Certificado nuevo (svm_1_cluster_1892EAF8B8E7D247) ← Recién instalado

DESPUÉS:
  [1] Certificado nuevo (svm_1_cluster_1892EAF8B8E7D247) ← Único certificado
```

---

## Casos de uso

### ✅ Workflow completo de renovación de certificados:

1. **Opción 1**: Generar nuevo CSR
   ```
   → Crear CSR y clave privada
   → Enviar CSR a la CA
   ```

2. **Opción 2**: Instalar certificado nuevo firmado
   ```
   → Recibir certificado de la CA
   → Instalar en ONTAP
   → Ahora hay 2 certificados: antiguo + nuevo
   ```

3. **Opción 3**: Activar nuevo certificado y eliminar antiguo
   ```
   → Obtener serial numbers
   → Configurar SSL con el certificado nuevo
   → Eliminar el certificado antiguo
   → Solo queda el nuevo certificado activo
   ```

---

## Solución de problemas

### ⚠️ "Certificate not found with serial number"

**Causa:** El certificado con ese serial number no existe.

**Solución:**
1. Verifica los serial numbers con `security certificate show -vserver <svm>`
2. Asegúrate de que el certificado no fue eliminado previamente

### ⚠️ "Certificate may be in use" (Error 409)

**Causa:** El certificado está actualmente asignado a la configuración SSL.

**Solución:**
1. Primero modifica SSL para usar otro certificado
2. Luego intenta eliminar el certificado antiguo
3. El script ya hace esto automáticamente en el orden correcto

### ⚠️ "Not enough certificates found for SSL modification"

**Causa:** Solo hay un certificado (o menos) en la SVM.

**Solución:**
1. Primero instala un nuevo certificado con la **Opción 2**
2. Luego ejecuta la **Opción 3**

### ⚠️ "SSL modification failed"

**Causa:** La configuración SSL no se pudo modificar.

**Solución:**
1. Verifica que el segundo certificado existe
2. Verifica los parámetros en config.yaml
3. El certificado no se eliminará si SSL modify falla (por seguridad)

### ⚠️ "Certificate deletion failed"

**Causa:** El certificado no se pudo eliminar (pero SSL ya fue modificado).

**Solución:**
1. El nuevo certificado ya está activo (SSL modify exitoso)
2. Elimina manualmente el certificado antiguo:
   ```bash
   security certificate delete -type server -vserver svm_1_cluster -serial <serial>
   ```

---

## Comandos CLI equivalentes (referencia)

```bash
# 1. Ver todos los certificados
security certificate show -vserver svm_1_cluster -instance

# 2. Modificar configuración SSL (con el segundo certificado)
security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true

# 3. Eliminar certificado antiguo (el primero)
security certificate delete -type server -vserver svm_1_cluster -ca vdc-ca -serial 16519C887ED0E2BF91150BC750220DC3A8B720D6 -common-name certificate

# 4. Verificar certificados restantes
security certificate show -vserver svm_1_cluster

# 5. Verificar configuración SSL
security ssl show -vserver svm_1_cluster
```

---

## Seguridad y mejores prácticas

### 🔒 Orden de operaciones

El script ejecuta las operaciones en el orden correcto para evitar problemas:

1. ✅ **Primero**: Modifica SSL para usar el certificado nuevo
2. ✅ **Después**: Elimina el certificado antiguo

**¿Por qué este orden?**
- Si eliminas primero y falla: Te quedas sin certificado SSL
- Si modificas primero y falla la eliminación: Al menos tienes SSL funcionando con el nuevo certificado

### ⚠️ Manejo de errores

El script está diseñado para ser seguro:

- Si **SSL modify falla**: No se elimina ningún certificado
- Si **Delete falla**: SSL ya está configurado con el nuevo certificado (estado válido)

### 📋 Verificación

Después de cada operación, el script:
- ✅ Verifica que el certificado existe/fue eliminado
- ✅ Muestra los certificados restantes
- ✅ Guarda logs detallados de todas las operaciones

---

## API REST utilizada

**Endpoints:**

1. **GET** `/api/security/certificates` - Obtener certificados
2. **GET** `/api/security/certificates/{uuid}` - Buscar certificado específico
3. **DELETE** `/api/security/certificates/{uuid}` - Eliminar certificado

**Documentación oficial:**
- https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/security_certificate.html
- https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/svm.html

---

## Resumen ejecutivo

### Lo que hace la Opción 3:

1. 📋 **Lee** todos los certificados de la SVM
2. 🔧 **Configura** SSL con el certificado nuevo (segundo)
3. 🗑️ **Elimina** el certificado antiguo (primero)
4. ✅ **Verifica** que todo quedó correcto

### Resultado final:

- ✅ Solo queda el certificado nuevo en la SVM
- ✅ SSL está configurado con el certificado nuevo
- ✅ Certificado antiguo fue eliminado
- ✅ Todo registrado en logs
