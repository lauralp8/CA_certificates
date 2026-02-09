# NetApp ONTAP Certificate Management Script

Script de Python para la generación automática de Certificate Signing Requests (CSR) en sistemas NetApp ONTAP usando la API REST.

## 📋 Descripción

Este script automatiza la generación de CSR (Certificate Signing Request) y pares de claves privadas en NetApp ONTAP, facilitando el proceso de obtención de certificados digitales firmados por una Autoridad de Certificación (CA).

## ✨ Características

- ✅ Generación de Certificate Signing Request (CSR)
- ✅ Generación de par de claves público/privadas
- ✅ Configuración de Subject Alternative Names (SAN)
- ✅ Configuración de Extended Key Usage
- ✅ Soporte para múltiples algoritmos de cifrado (RSA, EC)
- ✅ Funciones hash configurables (SHA256, SHA384, SHA512)
- ✅ Validación completa de parámetros
- ✅ Guardado automático de logs en formato JSON
- ✅ Manejo completo de errores

## 📦 Requisitos

- NetApp ONTAP 9.6 o superior
- Python 3.7 o superior
- Bibliotecas Python:
  - `netapp-ontap`
  - `PyYAML`

## 🔧 Instalación

1. Instalar las dependencias:
```bash
pip install netapp-ontap PyYAML
```

## ⚙️ Configuración

Edita el archivo `config.yaml` con los parámetros de tu entorno:

```yaml
# CLUSTER CONNECTION SETTINGS
cluster:
  host: cluster1.demo.netapp.com
  username: admin
  password: "your-password"

# CERTIFICATE SIGNING REQUEST (CSR) SETTINGS
certificate:
  common_name: SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm
  size: 2048
  algorithm: RSA
  hash_function: SHA256
  extended_key_usage:
    - serverAuth
    - clientAuth
  country: ES
  state: CORUNA
  locality: CORUNA
  dns_name: SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm
```

### Parámetros del Certificado

| Parámetro | Descripción | Requerido | Ejemplo |
|-----------|-------------|-----------|---------|
| `common_name` | Nombre común (FQDN) del certificado | ✅ Sí | `server.example.com` |
| `size` | Tamaño de la clave en bits | ✅ Sí | `2048`, `3072`, `4096` |
| `algorithm` | Algoritmo de cifrado | ✅ Sí | `RSA`, `EC` |
| `hash_function` | Función hash | ✅ Sí | `SHA256`, `SHA384`, `SHA512` |
| `extended_key_usage` | Usos extendidos del certificado | ✅ Sí | `[serverAuth, clientAuth]` |
| `country` | Código del país (2 letras) | ✅ Sí | `ES`, `US`, `UK` |
| `state` | Estado o provincia | ✅ Sí | `CORUNA`, `California` |
| `locality` | Ciudad o localidad | ✅ Sí | `CORUNA`, `San Francisco` |
| `dns_name` | Nombres DNS alternativos | ✅ Sí | `server.example.com` |
| `organization` | Nombre de la organización | ❌ No | `My Company` |
| `organizational_unit` | Unidad organizativa | ❌ No | `IT Department` |
| `email` | Correo electrónico de contacto | ❌ No | `admin@example.com` |
| `ip` | Direcciones IP alternativas | ❌ No | `[10.0.0.1, 10.0.0.2]` |
| `uri` | URIs alternativos | ❌ No | `[https://example.com]` |
| `key_usage` | Usos de la clave | ❌ No | `[digitalSignature, keyEncipherment]` |

## 🚀 Uso

Ejecuta el script:

```bash
python ca_certificates.py
```

El script ejecutará los siguientes pasos:

1. ✅ Carga la configuración desde `config.yaml`
2. ✅ Valida los parámetros requeridos
3. ✅ Establece conexión con el cluster NetApp
4. ✅ Genera el CSR y el par de claves
5. ✅ Muestra el CSR y la clave privada generados
6. ✅ Guarda los resultados en `logs/certificate_csr_YYYYMMDD_HHMMSS.json`
7. ✅ Genera backup de logs de eventos del cluster

## 📊 Salida del Script

El script generará:

1. **Certificate Signing Request (CSR)**: Un archivo en formato PEM que debes enviar a tu CA
2. **Private Key**: La clave privada correspondiente (¡guárdala de forma segura!)
3. **Log JSON**: Un archivo JSON con toda la información de la solicitud

### Ejemplo de salida:

```
======================================================================
  NetApp ONTAP Certificate Management Script
  Using NetApp ONTAP Python Client Library
======================================================================

[*] Initializing Certificate Signing Request workflow...
[+] Config.yaml loader: config.yaml
[+] Configuration loaded successfully
[+] Target cluster: cluster1.demo.netapp.com

[*] Establishing connection to cluster: cluster1.demo.netapp.com
[+] Connection successful!
[+] Cluster name: cluster1
[+] ONTAP version: NetApp Release 9.12.1

[*] Generating Certificate Signing Request (CSR)...
[+] Certificate details:
    - Common Name: SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm
    - Subject: C=ES,ST=CORUNA,L=CORUNA,CN=SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm
    - Algorithm: RSA
    - Key Size: 2048 bits
    - Hash Function: SHA256
    - Extended Key Usage: serverauth, clientauth
    - DNS Names: SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm

[+] CSR generated successfully!

[SUCCESS] Certificate Signing Request generated successfully!
[+] The CSR and private key have been saved to the logs/ directory
[+] Submit the CSR to your Certificate Authority to obtain a signed certificate
```

## 📁 Estructura de Archivos

```
CA_certificates/
├── ca_certificates.py      # Script principal
├── config.yaml             # Archivo de configuración
├── README.md              # Este archivo
└── logs/                  # Directorio de logs (se crea automáticamente)
    └── certificate_csr_YYYYMMDD_HHMMSS.json
```

## 🔒 Seguridad

⚠️ **IMPORTANTE**:
- La clave privada generada es **muy sensible**
- Guárdala en un lugar seguro
- No la compartas con nadie
- Será necesaria cuando instales el certificado firmado

## 📝 Equivalencia con CLI de ONTAP

Este script implementa el siguiente comando de ONTAP:

```bash
security certificate generate-csr \
  -common-name SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm \
  -size 2048 \
  -algorithm RSA \
  -hash-function SHA256 \
  -extended-key-usage serverAuth,clientAuth \
  -country ES \
  -state CORUNA \
  -locality CORUNA \
  -dns-name SVMv2-XXXXXX-RHOSO_COR_NAS01-NAS.es-north-1.cc.vdc.adm
```

## 🐛 Troubleshooting

### Error: "Missing required fields"
- Verifica que todos los campos requeridos estén en `config.yaml`
- Revisa que no haya errores de sintaxis YAML

### Error: "Connection failed"
- Verifica la conectividad de red con el cluster
- Confirma las credenciales en `config.yaml`
- Asegúrate de que el usuario tenga permisos suficientes

### Error: "NetApp API error"
- Revisa que la versión de ONTAP sea compatible (9.6+)
- Verifica los logs para más detalles del error

## 📚 Referencias

- [NetApp ONTAP REST API Documentation](https://library.netapp.com/ecmdocs/ECMLP3351667/html/)
- [NetApp ONTAP Python Client Library](https://pypi.org/project/netapp-ontap/)
- [Certificate Management Best Practices](https://docs.netapp.com/us-en/ontap/authentication/index.html)

## 📄 Licencia

Este script es proporcionado tal cual, sin garantías de ningún tipo.

## 👤 Autor

NetApp ONTAP Automation Team

---

**Versión**: 1.0.0  
**Última actualización**: 2026-02-09
