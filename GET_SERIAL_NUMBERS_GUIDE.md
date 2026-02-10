# Guía: Obtener Serial Numbers de Certificados

## Opción 3 del Menú: Get Serial Numbers from Certificates

### ¿Qué hace esta función?

La **Opción 3** ejecuta el comando:
```bash
security certificate show -vserver svm_1_cluster -instance
```

Y extrae todos los **serial numbers** de los certificados instalados en la SVM.

---

## Uso

### 1️⃣ Configuración requerida

En `config.yaml`, asegúrate de tener configurado:

```yaml
svm:
  name: svm_1_cluster  # Nombre de tu SVM
```

### 2️⃣ Ejecutar la opción 3

1. Ejecuta el script: `python ca_certificates.py`
2. Selecciona la **Opción 3** del menú
3. El script automáticamente:
   - ✅ Consulta todos los certificados de la SVM
   - ✅ Extrae los serial numbers
   - ✅ Los muestra en pantalla
   - ✅ Guarda los resultados en `logs/serial_numbers_*.json`

---

## Salida esperada

```
======================================================================
  CERTIFICATE SHOW - SVM: svm_1_cluster
======================================================================

Certificate #1:
----------------------------------------------------------------------
Certificate Name: rhoso
Common Name: certificate
Serial Number: 1A2B3C4D5E6F7G8H
Type: server
CA: vdc-ca
Expiry Time: 2027-02-09 10:30:00
Hash Function: sha256
Key Size: 2048 bits
UUID: 12345678-1234-1234-1234-123456789012

Certificate #2:
----------------------------------------------------------------------
Certificate Name: default-ca
Common Name: cluster1.demo.netapp.com
Serial Number: 9H8G7F6E5D4C3B2A
Type: server-ca
CA: cluster1.demo.netapp.com
Expiry Time: 2028-01-01 00:00:00
Hash Function: sha256
Key Size: 2048 bits
UUID: 87654321-4321-4321-4321-210987654321

======================================================================

======================================================================
  EXTRACTED SERIAL NUMBERS
======================================================================

Total certificates found: 2
Certificates with serial numbers: 2

[+] Serial Numbers:

    [1] 1A2B3C4D5E6F7G8H
    [2] 9H8G7F6E5D4C3B2A

======================================================================

[SUCCESS] Serial numbers retrieved successfully!
[+] Results saved to logs/serial_numbers_20260210_143025.json
```

---

## Archivo de log generado

El archivo `logs/serial_numbers_*.json` contiene:

```json
{
  "operation": "get_serial_numbers",
  "svm_name": "svm_1_cluster",
  "total_certificates": 2,
  "total_serial_numbers": 2,
  "serial_numbers": [
    "1A2B3C4D5E6F7G8H",
    "9H8G7F6E5D4C3B2A"
  ],
  "certificate_details": [
    {
      "certificate_name": "rhoso",
      "common_name": "certificate",
      "serial_number": "1A2B3C4D5E6F7G8H",
      "type": "server",
      "ca": "vdc-ca",
      "expiry_time": "2027-02-09 10:30:00",
      "uuid": "12345678-1234-1234-1234-123456789012"
    },
    {
      "certificate_name": "default-ca",
      "common_name": "cluster1.demo.netapp.com",
      "serial_number": "9H8G7F6E5D4C3B2A",
      "type": "server-ca",
      "ca": "cluster1.demo.netapp.com",
      "expiry_time": "2028-01-01 00:00:00",
      "uuid": "87654321-4321-4321-4321-210987654321"
    }
  ],
  "timestamp": "2026-02-10 14:30:25"
}
```

---

## Casos de uso

### ✅ Cuándo usar esta función:

- **Verificar certificados instalados** en una SVM
- **Obtener serial numbers** para operaciones de configuración SSL
- **Auditoría de certificados** - ver todos los certificados activos
- **Preparación para otros comandos** que requieren serial numbers

### 📋 Información que obtienes:

- ✅ **Serial Numbers** de todos los certificados
- ✅ Nombre del certificado
- ✅ Common Name (CN)
- ✅ Tipo de certificado (server, client, ca, etc.)
- ✅ Autoridad certificadora (CA)
- ✅ Fecha de expiración
- ✅ Algoritmo hash y tamaño de clave
- ✅ UUID del certificado

---

## Solución de problemas

### ⚠️ "No serial numbers found in any certificate"

**Posibles causas:**
- Los certificados no tienen serial number asignado
- Los certificados no se instalaron correctamente
- La SVM no tiene certificados instalados

**Solución:**
1. Verifica que la SVM tenga certificados instalados
2. Instala un certificado usando la Opción 2 del menú
3. Vuelve a ejecutar la Opción 3

### ⚠️ "Not Found - SVM may not exist"

**Causa:** El nombre de la SVM en `config.yaml` no es correcto

**Solución:**
1. Verifica el nombre correcto con: `vserver show`
2. Actualiza `svm.name` en `config.yaml`
3. Vuelve a intentar

### ⚠️ "Forbidden - User lacks required permissions"

**Causa:** El usuario no tiene permisos para ver certificados

**Solución:**
1. Asegúrate de que el usuario tiene rol de administrador de seguridad
2. Verifica con: `security login show -user-or-group-name admin`

---

## Comandos CLI equivalentes

```bash
# Mostrar todos los certificados de una SVM
security certificate show -vserver svm_1_cluster

# Mostrar detalles completos (instance)
security certificate show -vserver svm_1_cluster -instance

# Filtrar solo certificados de tipo server
security certificate show -vserver svm_1_cluster -type server

# Ver solo los serial numbers específicamente
security certificate show -vserver svm_1_cluster -fields serial
```

---

## Flujo de trabajo completo

**Workflow típico de gestión de certificados:**

1. **Opción 1**: Generar CSR
   ```
   → Genera CSR y clave privada
   → Enviar CSR a la CA
   ```

2. **Opción 2**: Instalar certificado firmado
   ```
   → Recibir certificado de la CA
   → Pegar en public_certificate.crt
   → Instalar en ONTAP
   ```

3. **Opción 3**: Verificar instalación
   ```
   → Obtener serial numbers
   → Verificar que el certificado está instalado
   → Guardar serial numbers para futuras operaciones
   ```

---

## API REST utilizada

**Endpoint:** `GET /api/security/certificates`

**Filtros:**
- `svm.name`: Nombre de la SVM

**Campos retornados:**
- name (certificate name)
- common_name
- serial_number ⭐
- type
- ca
- expiry_time
- hash_function
- key_size
- uuid

**Documentación oficial:**
https://library.netapp.com/ecmdocs/ECMLP3351667/html/resources/security_certificate.html
