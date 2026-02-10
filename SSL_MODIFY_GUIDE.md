# Guía: Modificación SSL de Certificados

## Opción 3 del Menú: Get Serial Numbers & Modify SSL Certificate

### ¿Qué hace esta función?

La **Opción 3** ejecuta un flujo completo de dos pasos:

1. **Obtiene serial numbers** de todos los certificados:
   ```bash
   security certificate show -vserver svm_1_cluster -instance
   ```

2. **Modifica la configuración SSL** usando el **segundo serial number**:
   ```bash
   security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial <serial_number> -server-enabled true
   ```

---

## Uso

### 1️⃣ Configuración requerida

En `config.yaml`, asegúrate de tener todos estos parámetros configurados:

```yaml
# SVM Settings
svm:
  name: svm_1_cluster  # Nombre de tu SVM

# SSL Configuration (REQUERIDO para la opción 3)
ssl:
  ca_name: vdc-ca  # Nombre de la CA del certificado
  server_enabled: true  # Habilitar servidor SSL (true/false)

# Certificate Settings
certificate:
  common_name: certificate  # Common name del certificado
  # ... otros parámetros ...
```

### 2️⃣ Ejecutar la opción 3

1. Ejecuta el script: `python ca_certificates.py`
2. Selecciona la **Opción 3** del menú
3. El script automáticamente:
   - ✅ Consulta todos los certificados de la SVM
   - ✅ Extrae los serial numbers
   - ✅ **Selecciona el segundo serial number** (índice [2])
   - ✅ Modifica la configuración SSL usando ese certificado
   - ✅ Guarda los resultados en logs

---

## Flujo de ejecución

### Paso 1: Obtención de Serial Numbers

```
======================================================================
  CERTIFICATE SHOW - SVM: svm_1_cluster
======================================================================

Certificate #1:
----------------------------------------------------------------------
Certificate Name: svm_1_cluster_default
Common Name: svm_1_cluster
Serial Number: A1B2C3D4E5F6G7H8
Type: server
...

Certificate #2:
----------------------------------------------------------------------
Certificate Name: svm_1_cluster_1892EAF8B8E7D247
Common Name: certificate
Serial Number: 1892EAF8B8E7D247  ⭐ (Este se usará para SSL modify)
Type: server
CA: vdc-ca
...

======================================================================
  EXTRACTED SERIAL NUMBERS
======================================================================

[+] Serial Numbers:

    [1] A1B2C3D4E5F6G7H8 - Certificate Name: svm_1_cluster_default
    [2] 1892EAF8B8E7D247 - Certificate Name: svm_1_cluster_1892EAF8B8E7D247 ⭐

======================================================================
```

### Paso 2: Modificación SSL

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
[*] CLI Equivalent: security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true

[+] SSL Modify Command:
    security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true

[+] Certificate found with UUID: 12345678-1234-1234-1234-123456789012
[+] Certificate is valid for SSL modification

[STEP 3/3] Verification...
[*] Retrieving current SSL certificates...

======================================================================
  SSL CERTIFICATES - SVM: svm_1_cluster
======================================================================

[1] SSL Certificate:
    Name: svm_1_cluster_1892EAF8B8E7D247
    Common Name: certificate
    Serial Number: 1892EAF8B8E7D247
    CA: vdc-ca
    Type: server

======================================================================
[INFO] Total SSL certificates: 1

[SUCCESS] SSL modification command generated successfully!
```

---

## Parámetros del comando SSL Modify

| Parámetro | Fuente en config.yaml | Ejemplo | Descripción |
|-----------|----------------------|---------|-------------|
| `-vserver` | `svm.name` | `svm_1_cluster` | Nombre de la SVM |
| `-ca` | `ssl.ca_name` | `vdc-ca` | Nombre de la Autoridad Certificadora |
| `-common-name` | `certificate.common_name` | `certificate` | Common Name del certificado |
| `-serial` | Segundo serial number del show | `1892EAF8B8E7D247` | Serial number del certificado |
| `-server-enabled` | `ssl.server_enabled` | `true` | Habilitar/deshabilitar servidor SSL |

---

## Archivos de log generados

### 1. `logs/serial_numbers_*.json`

Contiene todos los serial numbers encontrados:

```json
{
  "operation": "get_serial_numbers",
  "svm_name": "svm_1_cluster",
  "total_certificates": 2,
  "total_serial_numbers": 2,
  "serial_numbers": [
    "A1B2C3D4E5F6G7H8",
    "1892EAF8B8E7D247"
  ],
  "certificate_details": [
    {
      "certificate_name": "svm_1_cluster_default",
      "common_name": "svm_1_cluster",
      "serial_number": "A1B2C3D4E5F6G7H8",
      "type": "server",
      "ca": "svm_1_cluster",
      "expiry_time": "2027-01-01 00:00:00",
      "uuid": "..."
    },
    {
      "certificate_name": "svm_1_cluster_1892EAF8B8E7D247",
      "common_name": "certificate",
      "serial_number": "1892EAF8B8E7D247",
      "type": "server",
      "ca": "vdc-ca",
      "expiry_time": "2027-02-09 10:30:00",
      "uuid": "..."
    }
  ],
  "timestamp": "2026-02-10 14:30:25"
}
```

### 2. `logs/ssl_modify_*.json`

Contiene los detalles del comando SSL modify:

```json
{
  "operation": "ssl_modify",
  "svm_name": "svm_1_cluster",
  "ca_name": "vdc-ca",
  "common_name": "certificate",
  "serial_number": "1892EAF8B8E7D247",
  "server_enabled": true,
  "cli_command": "security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true",
  "timestamp": "2026-02-10 14:30:30"
}
```

---

## ¿Por qué se usa el segundo serial number?

Típicamente en NetApp ONTAP:
- **Primer certificado** (índice [1]): Certificado por defecto de la SVM
- **Segundo certificado** (índice [2]): Certificado personalizado instalado (el que instalaste con la opción 2)

El script automáticamente selecciona el segundo para aplicar la configuración SSL al certificado que acabas de instalar.

---

## Casos de uso

### ✅ Flujo completo de certificados:

1. **Opción 1**: Generar CSR
   ```
   → Crear CSR y clave privada
   → Enviar CSR a la CA
   ```

2. **Opción 2**: Instalar certificado firmado
   ```
   → Recibir certificado de la CA
   → Instalar en ONTAP
   ```

3. **Opción 3**: Configurar SSL con el nuevo certificado
   ```
   → Obtener serial numbers
   → Aplicar configuración SSL al certificado instalado
   → Verificar configuración
   ```

---

## Solución de problemas

### ⚠️ "Not enough certificates found for SSL modification"

**Causa:** Solo hay un certificado en la SVM (o menos).

**Solución:**
1. Primero ejecuta la **Opción 2** para instalar un certificado
2. Luego ejecuta la **Opción 3** para configurar SSL

### ⚠️ "No SSL configuration found in config.yaml"

**Causa:** Falta la sección `ssl` en config.yaml.

**Solución:** Agrega esta sección a config.yaml:
```yaml
ssl:
  ca_name: vdc-ca
  server_enabled: true
```

### ⚠️ "No common_name found in certificate section"

**Causa:** Falta el campo `common_name` en la sección `certificate`.

**Solución:** Agrega `common_name` a config.yaml:
```yaml
certificate:
  common_name: certificate
  # ... otros campos ...
```

### ⚠️ "Certificate not found with serial number"

**Causa:** El certificado con ese serial number no existe en la SVM.

**Solución:**
1. Verifica que el certificado se instaló correctamente con la Opción 2
2. Ejecuta `security certificate show -vserver <svm>` para verificar

---

## Comandos CLI equivalentes (referencia)

```bash
# 1. Ver todos los certificados
security certificate show -vserver svm_1_cluster -instance

# 2. Modificar configuración SSL
security ssl modify -vserver svm_1_cluster -ca vdc-ca -common-name certificate -serial 1892EAF8B8E7D247 -server-enabled true

# 3. Ver configuración SSL actual
security ssl show -vserver svm_1_cluster

# 4. Ver detalles de un certificado específico
security certificate show -vserver svm_1_cluster -serial 1892EAF8B8E7D247 -instance
```

---

## Notas importantes

### 📝 Sobre la API REST de NetApp

El comando `security ssl modify` no tiene un endpoint REST directo en la API de NetApp ONTAP. Por lo tanto, el script:

1. ✅ **Valida** todos los parámetros
2. ✅ **Genera** el comando CLI correcto
3. ✅ **Guarda** el comando en logs
4. ✅ **Verifica** que el certificado existe
5. ✅ **Muestra** los certificados SSL actuales

Para **ejecutar el comando** completo, puede que necesites:
- Acceso CLI al cluster de NetApp
- O usar el CLI passthrough de la API REST

### 🔒 Seguridad

- El comando modifica la configuración SSL de la SVM
- Asegúrate de que el certificado es válido y está firmado por una CA confiable
- El parámetro `server_enabled: true` habilita el servidor SSL

### ⚙️ Parámetros configurables

Todos los parámetros del comando se toman de `config.yaml`:
- `svm.name` → Nombre de la SVM
- `ssl.ca_name` → Nombre de la CA
- `ssl.server_enabled` → Habilitar/deshabilitar SSL
- `certificate.common_name` → Common name del certificado
- Serial number → Se obtiene automáticamente del segundo certificado

---

## API REST utilizada

**Endpoints:**
- `GET /api/security/certificates` - Obtener certificados
- `GET /api/security/certificates/{uuid}` - Verificar certificado específico

**Documentación oficial:**
- https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/security_certificate.html
- https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/svm.html
