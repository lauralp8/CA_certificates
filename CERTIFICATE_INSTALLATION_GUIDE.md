# Guía de Instalación de Certificados

## Proceso paso a paso

### 1️⃣ Generar CSR (Opción 1 del menú)

Ejecuta la **Opción 1** del menú para generar el Certificate Signing Request (CSR).

Esto creará un archivo en `csr_certificates/certificate_and_key_YYYYMMDD_HHMMSS.txt` que contiene:
- **Certificate Signing Request (CSR)** - Enviar a la CA
- **Private Key** - Guardar de forma segura

### 2️⃣ Obtener certificado firmado de la CA

1. Copia el **CSR** del archivo generado
2. Envíalo a tu Autoridad de Certificación (CA)
3. La CA te devolverá un **certificado firmado**

### 3️⃣ Preparar archivos para instalación

#### Archivo: `public_certificate.crt`

Abre el archivo `public_certificate.crt` y **reemplaza todo el contenido** con el certificado firmado que recibiste de la CA.

**Formato esperado:**
```
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKJ6fL9PqGH8MA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkVTMQ8wDQYDVQQIDAZDT1JVTkExDzANBgNVBAcMBkNPUlVOQTEUMBIGA1UE
... (varias líneas de texto base64) ...
-----END CERTIFICATE-----
```

#### Archivo: `private_key.key`

Abre el archivo `private_key.key` y **reemplaza todo el contenido** con la clave privada que se generó en el paso 1.

**Formato esperado:**
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC8hKEFqW4zGNPb
xH9jKPJvT0pzFQYqGxJ0m+8B7xYtYmHhFI3kJGHkJ9BqQZJpXqYvN5wH3gJ8pQYv
... (varias líneas de texto base64) ...
-----END PRIVATE KEY-----
```

**⚠️ IMPORTANTE:** 
- Copia el contenido **incluyendo** las líneas `-----BEGIN` y `-----END`
- Asegúrate de que no haya espacios extra al principio o final
- Mantén todos los saltos de línea tal como están

### 4️⃣ Verificar configuración

Revisa que `config.yaml` tenga los siguientes parámetros configurados:

```yaml
svm:
  name: svm_1_cluster  # Nombre de tu SVM

certificate:
  cert_name: rhoso  # Nombre para el certificado en ONTAP
  type: server  # Tipo de certificado
  public_certificate_file: public_certificate.crt
  private_key_file: private_key.key
```

### 5️⃣ Instalar certificado (Opción 2 del menú)

Ejecuta la **Opción 2** del menú para instalar el certificado.

El script automáticamente:
1. ✅ Lee el certificado público de `public_certificate.crt`
2. ✅ Lee la clave privada de `private_key.key`
3. ✅ Instala el certificado en ONTAP usando la API REST
4. ✅ Verifica que la instalación fue exitosa

**Equivalente al comando CLI:**
```bash
security certificate install -vserver svm_1_cluster -type server -cert-name rhoso
```

### 6️⃣ Limpieza post-instalación

**Por seguridad, después de instalar exitosamente:**

1. ✅ **Haz backup** de `private_key.key` en un lugar seguro
2. ❌ **Elimina** `private_key.key` de este directorio
3. ✅ Mantén una copia del certificado firmado para referencia

---

## Solución de problemas

### Error: "Public certificate file not found"
- Verifica que el archivo `public_certificate.crt` existe en el directorio
- Revisa que el nombre coincida con `public_certificate_file` en config.yaml

### Error: "Invalid certificate format"
- Asegúrate de que el certificado empiece con `-----BEGIN CERTIFICATE-----`
- Verifica que no haya caracteres extra o espacios incorrectos
- Copia el certificado exactamente como lo recibiste de la CA

### Error: "Certificate validation failed"
- Verifica que el certificado y la clave privada coincidan
- Asegúrate de usar la misma clave privada que generaste con el CSR

### Error: "Certificate with this name already exists"
- Cambia el valor de `cert_name` en config.yaml
- O elimina el certificado existente primero

---

## Comandos CLI equivalentes (referencia)

```bash
# 1. Generar CSR (lo hace la Opción 1)
security certificate generate-csr -common-name certificate -size 2048 -country ES

# 2. Instalar certificado (lo hace la Opción 2)
security certificate install -vserver svm_1_cluster -type server -cert-name rhoso
  # Enter certificate: <pega public_certificate.crt>
  # Enter private key: <pega private_key.key>
  # Continue with root/intermediate certificates? n

# 3. Ver certificados instalados (lo hace la Opción 3)
security certificate show -vserver svm_1_cluster -instance
```
