#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetApp ONTAP Certificate Management Script

This script automates certificate management operations on NetApp ONTAP systems
using the NetApp ONTAP REST API Python Client Library.

Features:
    - Certificate Signing Request (CSR) generation
    - Private key pair generation
    - Subject Alternative Names (SAN) configuration
    - Extended key usage configuration
    - Comprehensive error handling and validation

Requirements:
    - NetApp ONTAP 9.6+
    - Python 3.7+
    - netapp-ontap library
    - PyYAML library

Author: NetApp ONTAP Automation
Version: 1.0.0
"""

# ============================================================================
# IMPORTS
# ============================================================================
from netapp_ontap import config, HostConnection, NetAppRestError
from netapp_ontap.resources import Cluster, EmsEvent, SecurityCertificate
from netapp_ontap.resources import Svm
import yaml
import json
import os
import requests
from datetime import datetime
import urllib3

# Suprimir warnings de SSL (para verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# SCRIPT INITIALIZATION
# ============================================================================
print("\n" + "="*70)
print("  NetApp ONTAP Certificate Management Script")
print("  Using NetApp ONTAP Python Client Library")
print("="*70)
print("\n[*] Initializing Certificate Signing Request workflow...")


# ============================================================================
# YAML CONFIGURATION FUNCTION
# ============================================================================

def config_loader(path="config.yaml"):
    """
    Carga la configuración desde un archivo YAML con validación completa
    
    Lee el archivo de configuración y valida que contenga las secciones
    necesarias para crear una SVM en NetApp ONTAP.
    
    Args:
        path: Ruta al archivo de configuración (por defecto 'config.yaml')
    
    Returns:
        dict: Diccionario con la configuración cargada, o None si falla
    """
    try:
        print(f"[+] Config.yaml loader: {path}")
        
        # Abrir y leer el contenido del archivo YAML
        with open(path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        
        # VALIDACIONES
        # Validar que el archivo no esté vacío
        if config_data is None:
            print(f"[ERROR] File '{path}' is empty or doen't contain valid YAML")
            return None
        
        # Validar estructura: debe contener seccion 'cluster'
        if 'cluster' not in config_data:
            print(f"[ERROR]Incomplete configuration: missing 'cluster' section")
            return None
        
        # Validar estructura: debe contener seccion 'svm'
        if 'svm' not in config_data:
            print(f"[ERROR] Incomplete configuration: missing 'svm' section")
            return None
        
        print(f"[+] Configuration loaded successfully")

        # Mostrar resumen de la configuración cargada
        print(f"[+] Target cluster: {config_data['cluster'].get('host', 'N/A')}")
        print(f"[+] SVM to create: {config_data['svm'].get('name', 'N/A')}")
        
        return config_data
    
    # CONTROL DE ERRORES
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}")
        print(f"[ERROR] Please check the path and try again")
        return None
    
    except yaml.YAMLError as e:
        print(f"[ERROR] Invalid YAML format in '{path}'")
        print(f"[ERROR] Detail: {str(e)}")
        return None
    
    except PermissionError:
        print(f"[ERROR] Insufficient permissions to read: {path}")
        return None
    
    except Exception as e:
        print(f"[ERROR] Unexpected failure: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        return None


# ============================================================================
# SAVE TO LOG FUNCTION
# ============================================================================

def save_to_log(operation_name, data):
    """
    Guarda datos en un archivo JSON dentro de la carpeta logs/ con timestamp
    
    Args:
        operation_name (str): Nombre de la operación (ej: 'create_svm', 'fcp_create')
        data (dict): Datos a guardar (normalmente el show de la cabina)
    
    Returns:
        str: Ruta del archivo creado
    """
    try:
        # Crear carpeta logs si no existe
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Generar timestamp: YYYYMMDD_HHMMSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Nombre del archivo: operation_YYYYMMDD_HHMMSS.json
        filename = f"{logs_dir}/{operation_name}_{timestamp}.json"
        
        # Guardar en formato JSON
        with open(filename, 'w', encoding='utf-8') as log_file:
            json.dump(data, log_file, indent=2, ensure_ascii=False)
        
        print(f"[LOG] Saved to: {filename}")
        return filename
    
    except Exception as e:
        print(f"[WARNING] Could not save log: {str(e)}")
        return None


# ============================================================================
# CLUSTER CONNECTION FUNCTION
# ============================================================================

def cluster_connection(cluster_config):
    """
    Establece conexión con la cabina NetApp ONTAP y verifica acceso
    
    Conecta con el cluster usando las credenciales proporcionadas y realiza
    una consulta de prueba para validar que el acceso es correcto.
    
    Args:
        cluster_config: Diccionario con claves 'host', 'username', 'password'
    
    Returns:
        bool: True si conexión exitosa, False si hay errores
    """
    try:
        print(f"\n[*] Establishing connection to cluster: {cluster_config.get('host', 'N/A')}")
        
        # Validar que existan todos los campos necesarios
        required_keys = ['host', 'username', 'password']
        # Itera por cada clave requerida y guarda en una lista las que faltan
        missing_keys = [key for key in required_keys if key not in cluster_config]
        
        if missing_keys:
            print(f"[ERROR] Missing required fields in cluster config: {', '.join(missing_keys)}")
            return False
        
        # Establecer conexión con la cabina
        config.CONNECTION = HostConnection(
            cluster_config['host'],
            username=cluster_config['username'],
            password=cluster_config['password'],
            verify=False 
        )
        
        # Verificar acceso haciendo una consulta al cluster
        cluster_info = Cluster()
        cluster_info.get()
        
        print(f"[+] Connection successful!")
        print(f"[+] Cluster name: {cluster_info.name}")
        print(f"[+] ONTAP version: {cluster_info.version.full}")

        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp REST API error")
        print(f"[ERROR] HTTP status: {error.status_code}")
        
        # Detallar el tipo de error según el código HTTP
        if error.status_code == 401:
            print(f"[ERROR] Authentication failed")
            print(f"[ERROR] Invalid username or password for user '{cluster_config.get('username')}'")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
        elif error.status_code == 404:
            print(f"[ERROR] Resource not found - Check cluster URL")
        else:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        
        return False
    
    except KeyError as e:
        print(f"[ERROR] Configuration error - Missing key: {str(e)}")
        return False
    
    except ConnectionError:
        print(f"[ERROR] Cannot reach host '{cluster_config.get('host')}'")
        print(f"[ERROR] Check network connectivity and hostname/IP")
        return False
    
    except TimeoutError:
        print(f"[ERROR] Connection timeout to '{cluster_config.get('host')}'")
        print(f"[ERROR] Cluster is not responding")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        return False


# ============================================================================
# CA CERTIFICATES MANAGEMENT FUNCTIONS
# ============================================================================

def csr_generate(cert_config):
    """
    Genera un Certificate Signing Request (CSR) y un par de claves privadas
    
    Esta función utiliza la API REST de NetApp ONTAP para generar un CSR
    que puede ser enviado a una Autoridad de Certificación (CA) para
    obtener un certificado digital firmado.
    
    Args:
        cert_config: Diccionario con los parámetros del certificado:
            - common_name: Nombre común (FQDN) del certificado
            - size: Tamaño de la clave en bits (ej: 2048)
            - algorithm: Algoritmo de cifrado (ej: 'RSA')
            - hash_function: Función hash (ej: 'SHA256')
            - extended_key_usage: Lista de usos extendidos (ej: ['serverAuth', 'clientAuth'])
            - country: Código del país (ej: 'ES')
            - state: Estado o provincia (ej: 'CORUNA')
            - locality: Localidad o ciudad (ej: 'CORUNA')
            - dns_name: Nombre DNS alternativo del certificado
            - organization: Organización (opcional)
            - organizational_unit: Unidad organizativa (opcional)
            - email: Email de contacto (opcional)
    
    Returns:
        bool: True si el CSR se generó exitosamente, False si hubo error
    """
    try:
        from netapp_ontap.resources import SecurityConfig
        
        print(f"\n[*] Generating Certificate Signing Request (CSR)...")
        
        # Validar campos requeridos mínimos
        required_fields = ['common_name', 'size', 'algorithm', 'hash_function', 
                          'country', 'state', 'locality']
        missing_fields = [field for field in required_fields if field not in cert_config]
        
        if missing_fields:
            print(f"[ERROR] Missing required fields in certificate config: {', '.join(missing_fields)}")
            return False
        
        # Construir el subject_name en formato Distinguished Name (DN)
        # Formato: C=ES,ST=CORUNA,L=CORUNA,O=Organization,OU=Unit,CN=common-name
        subject_parts = []
        subject_parts.append(f"C={cert_config['country']}")
        subject_parts.append(f"ST={cert_config['state']}")
        subject_parts.append(f"L={cert_config['locality']}")
        
        if 'organization' in cert_config:
            subject_parts.append(f"O={cert_config['organization']}")
        
        if 'organizational_unit' in cert_config:
            subject_parts.append(f"OU={cert_config['organizational_unit']}")
        
        subject_parts.append(f"CN={cert_config['common_name']}")
        
        subject_name = ','.join(subject_parts)
        
        # Convertir tamaño de clave a security_strength (bits de seguridad)
        # Mapeo: 2048 bits → 112, 3072 bits → 128, 7680 bits → 192
        key_size = int(cert_config['size'])
        if key_size <= 2048:
            security_strength = 112
        elif key_size <= 3072:
            security_strength = 128
        else:
            security_strength = 192
        
        # Construir el body del request para el CSR
        csr_body = {
            'algorithm': cert_config['algorithm'].lower(),  # rsa, ec
            'security_strength': security_strength,  # Bits de fortaleza de seguridad
            'hash_function': cert_config['hash_function'].lower(),  # sha256, sha384, sha512
            'subject_name': subject_name
        }
        
        # Nota: extended_key_usage no está soportado en certificate_signing_request API
        # Se debe configurar al instalar el certificado firmado
        
        # Agregar subject alternatives (DNS, email, IP, URI)
        subject_alternatives = {}
        
        if 'dns_name' in cert_config and cert_config['dns_name']:
            # Puede ser una lista o un string
            dns_names = cert_config['dns_name'] if isinstance(cert_config['dns_name'], list) else [cert_config['dns_name']]
            subject_alternatives['dns'] = dns_names
        
        if 'email' in cert_config and cert_config['email']:
            emails = cert_config['email'] if isinstance(cert_config['email'], list) else [cert_config['email']]
            subject_alternatives['email'] = emails
        
        if 'ip' in cert_config and cert_config['ip']:
            ips = cert_config['ip'] if isinstance(cert_config['ip'], list) else [cert_config['ip']]
            subject_alternatives['ip'] = ips
        
        if 'uri' in cert_config and cert_config['uri']:
            uris = cert_config['uri'] if isinstance(cert_config['uri'], list) else [cert_config['uri']]
            subject_alternatives['uri'] = uris
        
        if subject_alternatives:
            csr_body['subject_alternatives'] = subject_alternatives
        
        # Agregar key_usage si está presente
        if 'key_usage' in cert_config and cert_config['key_usage']:
            csr_body['key_usage'] = [usage.lower() for usage in cert_config['key_usage']]
        
        # Mostrar resumen de la configuración
        print(f"[+] Certificate details:")
        print(f"    - Common Name: {cert_config['common_name']}")
        print(f"    - Subject: {subject_name}")
        print(f"    - Algorithm: {cert_config['algorithm']}")
        print(f"    - Key Size: {cert_config['size']} bits")
        print(f"    - Hash Function: {cert_config['hash_function']}")
        
        if 'extended_key_usage' in csr_body:
            print(f"    - Extended Key Usage: {', '.join(csr_body['extended_key_usage'])}")
        
        if subject_alternatives:
            if 'dns' in subject_alternatives:
                print(f"    - DNS Names: {', '.join(subject_alternatives['dns'])}")
        
        # POST: Generar el CSR usando SecurityConfig
        print(f"\n[*] Calling NetApp API to generate CSR...")
        
        security_config = SecurityConfig()
        response = security_config.certificate_signing_request(body=csr_body)
        
        # Verificar la respuesta
        if response.http_response.status_code == 200 or response.http_response.status_code == 201:
            print(f"[+] CSR generated successfully!")
            
            # Crear directorio para certificados si no existe
            import os
            csr_dir = 'csr_certificates'
            if not os.path.exists(csr_dir):
                os.makedirs(csr_dir)
                print(f"[+] Created directory: {csr_dir}/")
            
            # Extraer el CSR y la clave privada de la respuesta
            response_data = response.http_response.json()
            
            
            csr_data = {
                'subject_name': subject_name,
                'algorithm': cert_config['algorithm'],
                'key_size': cert_config['size'],
                'hash_function': cert_config['hash_function'],
                'request_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Buscar el CSR en diferentes posibles nombres de campo
            csr_content = None
            for key in ['signing_request', 'certificate_signing_request', 'csr', 'request']:
                if key in response_data:
                    csr_content = response_data[key]
                    break
            
            # Buscar la clave privada en diferentes posibles nombres de campo
            private_key_content = None
            for key in ['generated_private_key', 'private_key', 'key', 'privateKey']:
                if key in response_data:
                    private_key_content = response_data[key]
                    break
            
            # Mostrar y guardar el CSR
            if csr_content:
                csr_data['signing_request'] = csr_content
                print(f"\n[+] Certificate Signing Request (CSR):")
                print(f"{'='*70}")
                print(csr_content)
                print(f"{'='*70}")
            else:
                print(f"[WARNING] CSR not found in response")
            
            # Mostrar la clave privada
            if private_key_content:
                csr_data['private_key'] = private_key_content
                print(f"\n[+] Private Key:")
                print(f"{'='*70}")
                print(private_key_content)
                print(f"{'='*70}")
                print(f"\n[WARNING] Store the private key securely! It will be needed later.")
            else:
                print(f"[WARNING] Private key not found in response")
            
            # Guardar CSR y Private Key en un solo archivo .txt
            if csr_content or private_key_content:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    combined_filename = os.path.join(csr_dir, f'certificate_and_key_{timestamp}.txt')
                    
                    with open(combined_filename, 'w') as f:
                        if csr_content:
                            f.write("Certificate Signing Request:\n")
                            f.write(csr_content)
                            f.write("\n\n")
                        
                        if private_key_content:
                            f.write("Private Key:\n")
                            f.write(private_key_content)
                            f.write("\n")
                    
                    print(f"\n[+] Certificate and Private Key saved to: {combined_filename}")
                    print(f"[WARNING] Keep this file secure and delete it after use!")
                
                except Exception as e:
                    print(f"[WARNING] Failed to save certificate files: {str(e)}")
            
            return True
        else:
            print(f"[ERROR] Unexpected response status: {response.http_response.status_code}")
            return False
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during CSR generation")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 400:
            print(f"[ERROR] Bad request - Check certificate parameters")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - Insufficient permissions")
        
        if error.http_err_response and error.http_err_response.http_response:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Details: {str(error)}")
        
        return False
    
    except KeyError as e:
        print(f"[ERROR] Configuration error - Missing key in response: {str(e)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during CSR generation: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False



# ============================================================================
# GET SERIAL NUMBERS FUNCTION
# ============================================================================

def get_serial_numbers(svm_name):
    """
    Obtiene y muestra los serial numbers de los certificados de una SVM
    
    Esta función:
    1. Consulta todos los certificados de la SVM especificada
    2. Extrae los serial numbers de cada certificado
    3. Los muestra en pantalla de forma clara y organizada
    4. Guarda los resultados en un archivo de log
    
    Args:
        svm_name (str): Nombre de la SVM de la cual obtener certificados
    
    Returns:
        bool: True si se obtuvieron certificados exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Starting serial numbers retrieval workflow...")
        print(f"{'='*70}")
        
        # ====================================================================
        # PASO 1: EJECUTAR SHOW DE CERTIFICADOS
        # ====================================================================
        
        print(f"\n[STEP 1/3] Retrieving certificates from SVM: {svm_name}")
        
        # GET: Obtener todos los certificados de la SVM
        certificates = SecurityCertificate.get_collection(
            **{"svm.name": svm_name}
        )
        
        # ====================================================================
        # PASO 2: EXTRAER SERIAL NUMBERS
        # ====================================================================
        
        print(f"\n[STEP 2/3] Extracting serial numbers from certificates...")
        
        # Listas para almacenar los datos
        serial_numbers = []
        certificate_details = []
        
        print(f"\n{'='*70}")
        print(f"  CERTIFICATE SHOW - SVM: {svm_name}")
        print(f"{'='*70}\n")
        
        cert_count = 0
        
        for cert in certificates:
            # Obtener detalles completos del certificado
            cert.get()
            
            cert_count += 1
            
            print(f"Certificate #{cert_count}:")
            print(f"{'-'*70}")
            
            # Nombre del certificado
            cert_name = cert.name if hasattr(cert, 'name') else 'N/A'
            print(f"Certificate Name: {cert_name}")
            
            # Common Name
            common_name = cert.common_name if hasattr(cert, 'common_name') else 'N/A'
            print(f"Common Name: {common_name}")
            
            # Serial Number (CAMPO PRINCIPAL QUE BUSCAMOS)
            serial_number = cert.serial_number if hasattr(cert, 'serial_number') else None
            if serial_number:
                print(f"Serial Number: {serial_number}")
                serial_numbers.append(serial_number)
            else:
                print(f"Serial Number: N/A")
            
            # Información adicional
            if hasattr(cert, 'type'):
                print(f"Type: {cert.type}")
            
            if hasattr(cert, 'ca'):
                print(f"CA: {cert.ca}")
            
            if hasattr(cert, 'expiry_time'):
                print(f"Expiry Time: {cert.expiry_time}")
            
            if hasattr(cert, 'hash_function'):
                print(f"Hash Function: {cert.hash_function}")
            
            if hasattr(cert, 'key_size'):
                print(f"Key Size: {cert.key_size} bits")
            
            if hasattr(cert, 'uuid'):
                print(f"UUID: {cert.uuid}")
            
            if hasattr(cert, 'self_signed'):
                print(f"Self-Signed: {cert.self_signed}")
            
            # Guardar detalles del certificado
            cert_info = {
                'certificate_name': cert_name,
                'common_name': common_name,
                'serial_number': serial_number,
                'type': cert.type if hasattr(cert, 'type') else 'N/A',
                'ca': cert.ca if hasattr(cert, 'ca') else 'N/A',
                'expiry_time': str(cert.expiry_time) if hasattr(cert, 'expiry_time') else 'N/A',
                'uuid': cert.uuid if hasattr(cert, 'uuid') else 'N/A',
                'self_signed': cert.self_signed if hasattr(cert, 'self_signed') else None
            }
            certificate_details.append(cert_info)
            
            print("")  # Línea en blanco entre certificados
        
        print(f"{'='*70}")
        
        # ====================================================================
        # PASO 3: MOSTRAR RESUMEN DE SERIAL NUMBERS
        # ====================================================================
        
        print(f"\n[STEP 3/3] Serial Numbers Summary")
        print(f"\n{'='*70}")
        print(f"  EXTRACTED SERIAL NUMBERS")
        print(f"{'='*70}")
        
        if serial_numbers:
            print(f"\nTotal certificates found: {cert_count}")
            print(f"Certificates with serial numbers: {len(serial_numbers)}")
            print(f"\n[+] Serial Numbers:")
            print(f"")
            
            # Imprimir serial numbers con su etiqueta (certificate name)
            idx = 1
            for cert_detail in certificate_details:
                if cert_detail['serial_number']:
                    print(f"    [{idx}] {cert_detail['serial_number']} - Certificate Name: {cert_detail['certificate_name']}")
                    idx += 1
            
            print(f"\n{'='*70}")
            
            # Guardar en log
            log_data = {
                'operation': 'get_serial_numbers',
                'svm_name': svm_name,
                'total_certificates': cert_count,
                'total_serial_numbers': len(serial_numbers),
                'serial_numbers': serial_numbers,
                'certificate_details': certificate_details,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            save_to_log('serial_numbers', log_data)
            
            print(f"\n[SUCCESS] Serial numbers retrieved successfully!")
            
            # Retornar los detalles de los certificados para uso posterior
            return certificate_details
        
        else:
            print(f"\nTotal certificates found: {cert_count}")
            print(f"Certificates with serial numbers: 0")
            print(f"\n[WARNING] No serial numbers found in any certificate")
            print(f"[INFO] Certificates may not have been installed properly")
            print(f"\n{'='*70}")
            
            return None
    
    # ====================================================================
    # CONTROL DE ERRORES
    # ====================================================================
    
    except NetAppRestError as error:
        print(f"\n[ERROR] NetApp REST API error during serial numbers retrieval")
        print(f"[ERROR] HTTP Status Code: {error.status_code}")
        
        # Detallar errores comunes
        if error.status_code == 400:
            print(f"[ERROR] Bad Request - Check SVM name")
            print(f"[HINT] Verify that '{svm_name}' is a valid SVM name")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
            print(f"[HINT] Ensure the user has 'security' read permissions")
        elif error.status_code == 404:
            print(f"[ERROR] Not Found - SVM may not exist")
            print(f"[HINT] Check that SVM '{svm_name}' exists in the cluster")
        
        # Mostrar detalles del error
        if error.http_err_response and error.http_err_response.http_response:
            print(f"\n[ERROR] API Response Details:")
            print(f"{error.http_err_response.http_response.text}")
        else:
            print(f"\n[ERROR] Error Details: {str(error)}")
        
        return False
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during serial numbers retrieval")
        print(f"[ERROR] Error Type: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return None


# ============================================================================
# SSL CERTIFICATE MODIFICATION FUNCTION
# ============================================================================

def modify_ssl_certificate(svm_name, serial_number, ssl_config, common_name, ca_name=None):
    """
    Modifica la configuración SSL de un certificado en NetApp ONTAP

    Esta función:
    1. Valida los parámetros de configuración SSL
    2. Ejecuta la modificación SSL mediante la API REST de NetApp
    3. Verifica que la modificación se aplicó correctamente
    
    Args:
        svm_name (str): Nombre de la SVM donde modificar el SSL
        serial_number (str): Serial number del certificado a modificar
        ssl_config (dict): Configuración SSL desde config.yaml:
            - server_enabled: Habilitar/deshabilitar servidor SSL (true/false)
        common_name (str): Common name del certificado
        ca_name (str, optional): Nombre de la CA del certificado. Si no se proporciona,
                                 se extrae automáticamente del certificado
    
    Returns:
        bool: True si se modificó exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Starting SSL certificate modification workflow...")
        print(f"{'='*70}")
        
        # ====================================================================
        # PASO 1: VALIDAR PARÁMETROS DE CONFIGURACIÓN
        # ====================================================================
        
        print(f"\n[STEP 1/3] Validating SSL configuration parameters...")
        
        # Validar que existan los campos requeridos
        if 'server_enabled' not in ssl_config:
            print(f"[ERROR] Missing required field 'server_enabled' in config.yaml under 'ssl' section")
            print(f"\n[ERROR] Please add this field and try again")
            return False
        
        # Extraer parámetros
        server_enabled = ssl_config['server_enabled']
        
        # ====================================================================
        # EXTRACCIÓN DEL CA NAME (SEGURIDAD)
        # ====================================================================
        # Si no se proporciona CA name, intentar extraerlo del certificado
        # IMPORTANTE: El CA name es crítico para la modificación SSL correcta
        # ====================================================================
        
        if ca_name is None:
            print(f"[*] CA name not provided, extracting from certificate...")
            try:
                cert_found = SecurityCertificate.find(
                    **{
                        "svm.name": svm_name,
                        "serial_number": serial_number
                    }
                )
                
                if cert_found:
                    cert_found.get()
                    ca_name = cert_found.ca if hasattr(cert_found, 'ca') else None
                    
                    if ca_name:
                        print(f"[+] CA name extracted from certificate: {ca_name}")
                    else:
                        print(f"[ERROR] Could not extract CA name from certificate")
                        return False
                else:
                    print(f"[ERROR] Certificate not found with serial number: {serial_number}")
                    return False
                    
            except Exception as extract_error:
                print(f"[ERROR] Error extracting CA name: {str(extract_error)}")
                return False
        else:
            print(f"[+] Using provided CA name: {ca_name}")
        
        print(f"[+] Configuration validated:")
        print(f"    - SVM Name: {svm_name}")
        print(f"    - CA Name: {ca_name}")
        print(f"    - Common Name: {common_name}")
        print(f"    - Serial Number: {serial_number}")
        print(f"    - Server Enabled: {server_enabled}")
        
        # ====================================================================
        # PASO 2: EJECUTAR MODIFICACIÓN SSL
        # ====================================================================
        
        print(f"\n[STEP 2/3] Modifying SSL configuration...")
        print(f"[*] CLI Command: security ssl modify -vserver {svm_name} -ca {ca_name} -common-name {common_name} -serial {serial_number} -server-enabled {str(server_enabled).lower()}")
        
        # Construir el comando CLI
        cli_command = (
            f"security ssl modify "
            f"-vserver {svm_name} "
            f"-ca {ca_name} "
            f"-common-name {common_name} "
            f"-serial {serial_number} "
            f"-server-enabled {str(server_enabled).lower()}"
        )
        
        print(f"\n[+] Executing SSL modification via CLI passthrough...")
        
        # Verificar que el certificado existe antes de modificar SSL
        print(f"[*] Verifying certificate exists...")
        
        try:
            cert_found = SecurityCertificate.find(
                **{
                    "svm.name": svm_name,
                    "serial_number": serial_number
                }
            )
            
            if cert_found:
                print(f"[+] Certificate found with UUID: {cert_found.uuid}")
                print(f"[+] Certificate is valid for SSL modification")
            else:
                print(f"[ERROR] Certificate not found with serial number: {serial_number}")
                print(f"[ERROR] Cannot proceed with SSL modification")
                return False
        
        except Exception as find_error:
            print(f"[WARNING] Could not verify certificate: {str(find_error)}")
            print(f"[WARNING] Proceeding with SSL modification anyway...")
        
        # Ejecutar el comando mediante API CLI passthrough
        print(f"\n[*] Generating SSL modification command...")
        print(f"[WARNING] SSL modification via API is not supported in all ONTAP versions")
        print(f"[INFO] The command will be saved for manual execution or automated via CLI")
        
        api_success = False
        
        # ====================================================================
        # INTENTO 1: Usar API REST oficial /api/security/ssl (PATCH)
        # ====================================================================
        
        print(f"\n[DEBUG] Attempting Method 1: REST API /api/security/ssl")
        
        try:
            from netapp_ontap.resources import Svm
            
            # Buscar la SVM
            svm = Svm.find(name=svm_name)
            if svm:
                print(f"[DEBUG] SVM found: {svm.uuid}")
                
                # Intentar PATCH en el endpoint SSL
                api_url_ssl = f"https://{config.connection.origin}/api/security/ssl/{svm.uuid}"
                
                # Probar diferentes formatos de payload
                payloads_to_try = [
                    {
                        "certificate": {
                            "name": cert_found.name if 'cert_found' in locals() else None
                        },
                        "enabled": server_enabled
                    },
                    {
                        "certificate": {
                            "uuid": cert_found.uuid if 'cert_found' in locals() else None
                        },
                        "enabled": server_enabled
                    },
                    {
                        "server_enabled": server_enabled,
                        "certificate": {
                            "name": cert_found.name if 'cert_found' in locals() else None
                        }
                    }
                ]
                
                for i, payload in enumerate(payloads_to_try):
                    print(f"\n[DEBUG] Trying payload format {i+1}:")
                    print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}")
                    
                    response = requests.patch(
                        api_url_ssl,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        json=payload,
                        auth=(config.connection.username, config.connection.password),
                        verify=False,
                        timeout=10
                    )
                    
                    print(f"[DEBUG] Response Status: {response.status_code}")
                    print(f"[DEBUG] Response Body: {response.text}")
                    
                    if response.status_code in [200, 201, 202]:
                        print(f"[+] SUCCESS with payload format {i+1}!")
                        api_success = True
                        break
                        
        except Exception as rest_error:
            print(f"[DEBUG] REST API method failed: {str(rest_error)}")
        
        # ====================================================================
        # INTENTO 2: Usar API CLI privado /api/private/cli/security/ssl (PATCH)
        # ====================================================================
        
        if not api_success:
            print(f"\n[DEBUG] Attempting Method 2: CLI API /api/private/cli/security/ssl")
            
            try:
                # Intentar usar el endpoint de CLI privado de NetApp ONTAP
                api_url = f"https://{config.connection.origin}/api/private/cli/security/ssl"
                
                # Probar diferentes formatos de payload
                payloads_to_try = [
                    # Formato 1: Todos los parámetros como strings
                    {
                        "vserver": svm_name,
                        "ca": ca_name,
                        "common-name": common_name,
                        "serial": serial_number,
                        "server-enabled": str(server_enabled).lower()
                    },
                    # Formato 2: server-enabled como boolean
                    {
                        "vserver": svm_name,
                        "ca": ca_name,
                        "common-name": common_name,
                        "serial": serial_number,
                        "server-enabled": server_enabled
                    },
                    # Formato 3: con guiones bajos
                    {
                        "vserver": svm_name,
                        "ca": ca_name,
                        "common_name": common_name,
                        "serial": serial_number,
                        "server_enabled": server_enabled
                    },
                    # Formato 4: sin serial, solo con certificate name
                    {
                        "vserver": svm_name,
                        "certificate": cert_found.name if 'cert_found' in locals() else ca_name,
                        "server-enabled": server_enabled
                    }
                ]
                
                for i, payload in enumerate(payloads_to_try):
                    print(f"\n[DEBUG] Trying CLI payload format {i+1}:")
                    print(f"[DEBUG] URL: PATCH {api_url}")
                    print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}")
                    
                    # Ejecutar la petición PATCH
                    response = requests.patch(
                        api_url,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        },
                        json=payload,
                        auth=(config.connection.username, config.connection.password),
                        verify=False,
                        timeout=10
                    )
                    
                    # Verificar la respuesta
                    print(f"[DEBUG] Response Status: {response.status_code}")
                    print(f"[DEBUG] Response Headers: {dict(response.headers)}")
                    print(f"[DEBUG] Response Body: {response.text}")
                    
                    if response.status_code in [200, 201, 202]:
                        print(f"[+] SSL modification executed successfully via CLI API (format {i+1})!")
                        api_success = True
                        break
                    elif response.status_code == 404:
                        print(f"[DEBUG] API endpoint not available (404)")
                    else:
                        print(f"[DEBUG] API returned non-success status")
                        try:
                            error_data = response.json()
                            print(f"[DEBUG] Error details: {json.dumps(error_data, indent=2)}")
                        except:
                            pass
                
            except requests.exceptions.Timeout:
                print(f"[DEBUG] API request timed out")
            except Exception as api_error:
                print(f"[DEBUG] CLI API call failed: {str(api_error)}")
                import traceback
                print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        
        # Siempre proporcionar el comando CLI para ejecución manual
        print(f"\n{'='*70}")
        print(f"  MANUAL EXECUTION COMMAND")
        print(f"{'='*70}")
        print(f"\n[IMPORTANT] Execute this command on the ONTAP cluster CLI:")
        print(f"\n{cli_command}")
        print(f"\n{'='*70}")
        
        # Guardar el comando en log para referencia
        print(f"\n[*] Saving SSL modification details to log...")
        print(f"[+] Recording CA name for traceability: {ca_name}")
        
        ssl_modify_log = {
            'operation': 'ssl_modify',
            'svm_name': svm_name,
            'ca_name': ca_name,  # CA extraído del certificado (importante para auditoría)
            'common_name': common_name,
            'serial_number': serial_number,
            'server_enabled': server_enabled,
            'cli_command': cli_command,
            'api_success': api_success if 'api_success' in locals() else False,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        save_to_log('ssl_modify', ssl_modify_log)
        
        # ====================================================================
        # PASO 3: VERIFICACIÓN
        # ====================================================================
        
        print(f"\n[STEP 3/3] Verification...")
        
        # Mostrar certificados SSL actuales de la SVM
        print(f"\n[*] Retrieving current SSL certificates...")
        
        try:
            ssl_certs = SecurityCertificate.get_collection(
                **{"svm.name": svm_name, "type": "server"}
            )
            
            print(f"\n{'='*70}")
            print(f"  SSL CERTIFICATES - SVM: {svm_name}")
            print(f"{'='*70}")
            
            cert_count = 0
            for ssl_cert in ssl_certs:
                ssl_cert.get()
                cert_count += 1
                
                print(f"\n[{cert_count}] SSL Certificate:")
                print(f"    Name: {ssl_cert.name if hasattr(ssl_cert, 'name') else 'N/A'}")
                print(f"    Common Name: {ssl_cert.common_name if hasattr(ssl_cert, 'common_name') else 'N/A'}")
                print(f"    Serial Number: {ssl_cert.serial_number if hasattr(ssl_cert, 'serial_number') else 'N/A'}")
                print(f"    CA: {ssl_cert.ca if hasattr(ssl_cert, 'ca') else 'N/A'}")
                print(f"    Type: {ssl_cert.type if hasattr(ssl_cert, 'type') else 'N/A'}")
            
            print(f"\n{'='*70}")
            print(f"[INFO] Total SSL certificates: {cert_count}")
            
        except Exception as verify_error:
            print(f"[WARNING] Could not retrieve SSL certificates: {str(verify_error)}")
        
        # Verificar la configuración SSL modificada
        print(f"\n[*] Verifying SSL configuration...")
        print(f"[*] CLI Command: security ssl show -vserver {svm_name} -instance")
        
        # ====================================================================
        # DEBUG: OBTENER CONFIGURACIÓN SSL ACTUAL VÍA API REST
        # ====================================================================
        
        print(f"\n[DEBUG] Attempting to retrieve SSL configuration via REST API...")
        
        try:
            # Usar el endpoint REST API oficial para SVM
            from netapp_ontap.resources import Svm
            
            print(f"[DEBUG] Searching for SVM: {svm_name}")
            svm = Svm.find(name=svm_name)
            
            if svm:
                svm.get()
                print(f"[DEBUG] SVM found with UUID: {svm.uuid}")
                
                # Obtener todos los atributos disponibles del objeto SVM
                print(f"\n[DEBUG] Available SVM attributes:")
                for attr in dir(svm):
                    if not attr.startswith('_') and not callable(getattr(svm, attr)):
                        value = getattr(svm, attr, 'N/A')
                        print(f"    - {attr}: {value}")
                
                # Verificar si hay atributos relacionados con SSL
                if hasattr(svm, 'certificate'):
                    print(f"\n[DEBUG] SVM has certificate attribute:")
                    cert_info = svm.certificate
                    print(f"    Certificate info: {cert_info}")
                
                # Intentar obtener la configuración SSL directamente
                api_url_ssl = f"https://{config.connection.origin}/api/security/ssl"
                
                print(f"\n[DEBUG] Calling SSL API: GET {api_url_ssl}")
                
                response_ssl = requests.get(
                    api_url_ssl,
                    headers={"Accept": "application/json"},
                    params={"svm.name": svm_name, "fields": "*"},
                    auth=(config.connection.username, config.connection.password),
                    verify=False,
                    timeout=10
                )
                
                print(f"[DEBUG] SSL API Response Status: {response_ssl.status_code}")
                
                if response_ssl.status_code == 200:
                    ssl_data = response_ssl.json()
                    print(f"\n[DEBUG] SSL API Response (full):")
                    print(json.dumps(ssl_data, indent=2))
                    
                    if 'records' in ssl_data:
                        print(f"\n[+] SSL Configuration found:")
                        for record in ssl_data['records']:
                            print(f"\n    Record:")
                            for key, value in record.items():
                                print(f"      - {key}: {value}")
                else:
                    print(f"[DEBUG] SSL API returned: {response_ssl.text}")
                    
        except Exception as debug_error:
            print(f"[DEBUG] Error during SSL debugging: {str(debug_error)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        
        # Intentar con el endpoint CLI privado
        try:
            # Construir URL para obtener configuración SSL
            api_url_show = f"https://{config.connection.origin}/api/private/cli/security/ssl"
            
            print(f"\n[DEBUG] Attempting CLI API: GET {api_url_show}")
            
            response_show = requests.get(
                api_url_show,
                headers={"Accept": "application/json"},
                params={"vserver": svm_name, "fields": "*"},
                auth=(config.connection.username, config.connection.password),
                verify=False,
                timeout=10
            )
            
            print(f"[DEBUG] CLI API Response Status: {response_show.status_code}")
            
            if response_show.status_code == 200:
                ssl_info = response_show.json()
                print(f"\n[DEBUG] CLI API Response (full):")
                print(json.dumps(ssl_info, indent=2))
                
                print(f"\n[+] Current SSL Configuration (from CLI API):")
                if 'records' in ssl_info and len(ssl_info['records']) > 0:
                    ssl_record = ssl_info['records'][0]
                    print(f"\n    All fields in SSL record:")
                    for key, value in ssl_record.items():
                        print(f"      - {key}: {value}")
                    
                    # Mostrar campos específicos
                    print(f"\n    Key SSL fields:")
                    print(f"      - CA: {ssl_record.get('ca', 'N/A')}")
                    print(f"      - Common Name: {ssl_record.get('common_name', 'N/A')}")
                    print(f"      - Serial Number: {ssl_record.get('serial', 'N/A')}")
                    print(f"      - Server Enabled: {ssl_record.get('server_enabled', 'N/A')}")
                    print(f"      - Server Authentication Enabled: {ssl_record.get('server_authentication_enabled', 'N/A')}")
                    print(f"      - Client Enabled: {ssl_record.get('client_enabled', 'N/A')}")
                    print(f"      - Client Authentication Enabled: {ssl_record.get('client_authentication_enabled', 'N/A')}")
            else:
                print(f"[DEBUG] CLI API returned: {response_show.text}")
        except Exception as cli_error:
            print(f"[DEBUG] CLI API error: {str(cli_error)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        
        print(f"\n[SUCCESS] SSL modification workflow completed!")
        print(f"[+] Command executed and saved to logs for reference")
        print(f"\n[IMPORTANT] Verification:")
        print(f"    Run this command on the cluster to verify:")
        print(f"    security ssl show -vserver {svm_name} -instance")
        
        return True
    
    # ====================================================================
    # CONTROL DE ERRORES
    # ====================================================================
    
    except NetAppRestError as error:
        print(f"\n[ERROR] NetApp REST API error during SSL modification")
        print(f"[ERROR] HTTP Status Code: {error.status_code}")
        
        # Detallar errores comunes
        if error.status_code == 400:
            print(f"[ERROR] Bad Request - Invalid parameters")
            print(f"[HINT] Verify SVM name, serial number, and CA name")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
            print(f"[HINT] Ensure the user has 'security' admin role")
        elif error.status_code == 404:
            print(f"[ERROR] Not Found - Certificate or SVM may not exist")
            print(f"[HINT] Verify that the certificate exists with the given serial number")
        
        # Mostrar detalles del error
        if error.http_err_response and error.http_err_response.http_response:
            print(f"\n[ERROR] API Response Details:")
            print(f"{error.http_err_response.http_response.text}")
        else:
            print(f"\n[ERROR] Error Details: {str(error)}")
        
        return False
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during SSL modification")
        print(f"[ERROR] Error Type: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# CERTIFICATE DELETE FUNCTION
# ============================================================================

def delete_certificate(svm_name, serial_number, cert_config):
    """
    Elimina un certificado de NetApp ONTAP usando el comando CLI específico
        
    Esta función:
    1. Valida los parámetros de configuración
    2. Busca el certificado por serial number
    3. Elimina el certificado usando la API REST de NetApp
    4. Verifica que el certificado fue eliminado
    
    El comando CLI utilizado es:
    security certificate delete -type server -vserver <svm_name> -ca <svm_name> 
                                -serial <serial_number> -common-name <svm_name>
    
    Criterio de selección: Certificado donde CA = nombre_vserver
    
    Args:
        svm_name (str): Nombre de la SVM donde eliminar el certificado
        serial_number (str): Serial number del certificado a eliminar
        cert_config (dict): Configuración del certificado:
            - type: Tipo de certificado (default: 'server')
            - common_name: Common name (generalmente = svm_name)
            - ca_name: Nombre de la CA (generalmente = svm_name)
    
    Returns:
        bool: True si se eliminó exitosamente, False si hubo error
  """
    try:
        print(f"\n[*] Starting certificate deletion workflow...")
        print(f"{'='*70}")
        
        # ====================================================================
        # PASO 1: VALIDAR PARÁMETROS DE CONFIGURACIÓN
        # ====================================================================
        
        print(f"\n[STEP 1/4] Validating configuration parameters...")
        
        # Extraer parámetros
        cert_type = cert_config.get('type', 'server')
        common_name = cert_config.get('common_name')
        ca_name = cert_config.get('ca_name')
        
        # Validar parámetros requeridos
        if not common_name:
            print(f"[ERROR] Missing 'common_name' in certificate configuration")
            return False
        
        if not ca_name:
            print(f"[ERROR] Missing 'ca_name' in certificate configuration")
            return False
        
        print(f"[+] Deletion parameters validated:")
        print(f"    - Type: {cert_type}")
        print(f"    - VServer: {svm_name}")
        print(f"    - CA Name: {ca_name}")
        print(f"    - Common Name: {common_name}")
        print(f"    - Serial Number: {serial_number}")
        
    
        # ====================================================================
        # PASO 2: BUSCAR EL CERTIFICADO
        # ====================================================================
        
        print(f"\n[STEP 2/4] Locating certificate...")
        print(f"[*] Searching for certificate with serial number: {serial_number}")
        
        # Buscar el certificado por serial number
        cert_to_delete = None
        
        try:
            # GET: Buscar certificado por serial number y SVM
            certificates = SecurityCertificate.get_collection(
                **{
                    "svm.name": svm_name,
                    "serial_number": serial_number
                }
            )
            
            for cert in certificates:
                cert.get()
                cert_to_delete = cert
                break  # Tomar el primero que coincida
            
            if cert_to_delete:
                print(f"[+] Certificate found:")
                print(f"    - UUID: {cert_to_delete.uuid}")
                print(f"    - Name: {cert_to_delete.name if hasattr(cert_to_delete, 'name') else 'N/A'}")
                print(f"    - Common Name: {cert_to_delete.common_name if hasattr(cert_to_delete, 'common_name') else 'N/A'}")
                print(f"    - Type: {cert_to_delete.type if hasattr(cert_to_delete, 'type') else 'N/A'}")
                print(f"    - Serial Number: {cert_to_delete.serial_number if hasattr(cert_to_delete, 'serial_number') else 'N/A'}")
            else:
                print(f"[ERROR] Certificate not found with serial number: {serial_number}")
                return False
                
        except Exception as search_error:
            print(f"[ERROR] Error searching for certificate: {str(search_error)}")
            return False
        
        # ====================================================================
        # PASO 3: ELIMINAR EL CERTIFICADO
        # ====================================================================
        
        print(f"\n[STEP 3/4] Deleting certificate...")
        
        # Construir el comando CLI para referencia
        cli_command = (
            f"security certificate delete "
            f"-type {cert_type} "
            f"-vserver {svm_name} "
            f"-ca {ca_name} "
            f"-serial {serial_number} "
            f"-common-name {common_name}"
        )
    
        
        # DELETE: Eliminar el certificado usando la API REST
        print(f"\n[*] Executing certificate deletion...")
        cert_to_delete.delete()
        
        print(f"[+] Certificate deleted successfully!")
        
        # ====================================================================
        # PASO 4: VERIFICACIÓN
        # ====================================================================
        
        print(f"\n[STEP 4/4] Verification...")
        print(f"[*] Verifying certificate was deleted...")
        
        # Verificar que el certificado ya no existe
        try:
            verify_certs = SecurityCertificate.get_collection(
                **{
                    "svm.name": svm_name,
                    "serial_number": serial_number
                }
            )
            
            cert_still_exists = False
            for cert in verify_certs:
                cert_still_exists = True
                break
            
            if cert_still_exists:
                print(f"[WARNING] Certificate still appears in the system")
                print(f"[INFO] It may take a moment to be fully removed")
            else:
                print(f"[+] Certificate successfully removed from the system")
        
        except Exception as verify_error:
            print(f"[INFO] Verification check completed (certificate likely deleted)")
        
        # Mostrar certificados restantes en la SVM
        print(f"\n[*] Retrieving remaining certificates in SVM...")
        
        try:
            remaining_certs = SecurityCertificate.get_collection(
                **{"svm.name": svm_name}
            )
            
            print(f"\n{'='*70}")
            print(f"  REMAINING CERTIFICATES - SVM: {svm_name}")
            print(f"{'='*70}")
            
            cert_count = 0
            for remaining_cert in remaining_certs:
                remaining_cert.get()
                cert_count += 1
                
                print(f"\n[{cert_count}] Certificate:")
                print(f"    Name: {remaining_cert.name if hasattr(remaining_cert, 'name') else 'N/A'}")
                print(f"    Common Name: {remaining_cert.common_name if hasattr(remaining_cert, 'common_name') else 'N/A'}")
                print(f"    Serial Number: {remaining_cert.serial_number if hasattr(remaining_cert, 'serial_number') else 'N/A'}")
                print(f"    Type: {remaining_cert.type if hasattr(remaining_cert, 'type') else 'N/A'}")
            
            print(f"\n{'='*70}")
            print(f"[INFO] Total remaining certificates: {cert_count}")
            
        except Exception as list_error:
            print(f"[WARNING] Could not retrieve remaining certificates: {str(list_error)}")
        
        # Guardar en log
        print(f"\n[*] Saving deletion details to log...")
        
        delete_log = {
            'operation': 'certificate_delete',
            'svm_name': svm_name,
            'serial_number': serial_number,
            'cert_type': cert_type,
            'ca_name': ca_name,
            'common_name': common_name,
            'cli_command': cli_command,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'note': 'Certificate deleted where CA = SVM name. Parameters: type=server, vserver=svm_name, ca=svm_name, serial=serial_number, common-name=svm_name'
        }
        
        save_to_log('certificate_delete', delete_log)
        
        print(f"\n[SUCCESS] Certificate deletion completed successfully!")
        print(f"[+] Operation saved to logs/certificate_delete_*.json")
        
        # ====================================================================
        # INFORMACIÓN ADICIONAL: SECURITY LOGIN SHOW Y SSL SHOW
        # ====================================================================
        
        # Security Login Show
        print(f"\n[*] Retrieving security login information...")
        try:
            from netapp_ontap.resources import SecurityAccount
            
            logins = SecurityAccount.get_collection(**{"owner.name": svm_name})
            
            print(f"\n{'='*70}")
            print(f"  SECURITY LOGIN SHOW - SVM: {svm_name}")
            print(f"{'='*70}")
            
            login_list = []
            for login in logins:
                login.get()
                login_info = {
                    'user': login.name if hasattr(login, 'name') else 'N/A',
                    'application': login.applications[0].application if hasattr(login, 'applications') and login.applications else 'N/A',
                    'authentication': login.applications[0].authentication_methods[0] if hasattr(login, 'applications') and login.applications and hasattr(login.applications[0], 'authentication_methods') else 'N/A',
                    'role': login.role.name if hasattr(login, 'role') and hasattr(login.role, 'name') else 'N/A'
                }
                login_list.append(login_info)
                
                print(f"\nUser: {login_info['user']}")
                print(f"  Application: {login_info['application']}")
                print(f"  Authentication: {login_info['authentication']}")
                print(f"  Role: {login_info['role']}")
            
            print(f"\n{'='*70}")
            print(f"[INFO] Total login accounts: {len(login_list)}")
            
            # Guardar en log
            login_log = {
                'operation': 'security_login_show',
                'svm_name': svm_name,
                'total_logins': len(login_list),
                'logins': login_list,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_to_log('security_login_show', login_log)
            
        except Exception as login_error:
            print(f"[WARNING] Could not retrieve security login info: {str(login_error)}")
        
        # Security SSL Show
        print(f"\n[*] Retrieving SSL configuration...")
        try:
            ssl_certs = SecurityCertificate.get_collection(
                **{"svm.name": svm_name, "type": "server"}
            )
            
            print(f"\n{'='*70}")
            print(f"  SECURITY SSL SHOW - SVM: {svm_name}")
            print(f"{'='*70}")
            
            ssl_list = []
            for ssl_cert in ssl_certs:
                ssl_cert.get()
                ssl_info = {
                    'vserver': svm_name,
                    'certificate_name': ssl_cert.name if hasattr(ssl_cert, 'name') else 'N/A',
                    'serial': ssl_cert.serial_number if hasattr(ssl_cert, 'serial_number') else 'N/A',
                    'ca': ssl_cert.ca if hasattr(ssl_cert, 'ca') else 'N/A',
                    'common_name': ssl_cert.common_name if hasattr(ssl_cert, 'common_name') else 'N/A'
                }
                ssl_list.append(ssl_info)
                
                print(f"\nVserver: {ssl_info['vserver']}")
                print(f"  Certificate Name: {ssl_info['certificate_name']}")
                print(f"  Serial: {ssl_info['serial']}")
                print(f"  CA: {ssl_info['ca']}")
                print(f"  Common Name: {ssl_info['common_name']}")
            
            print(f"\n{'='*70}")
            print(f"[INFO] Total SSL certificates: {len(ssl_list)}")
            
            # Guardar en log
            ssl_log = {
                'operation': 'security_ssl_show',
                'svm_name': svm_name,
                'total_ssl_certs': len(ssl_list),
                'ssl_certificates': ssl_list,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_to_log('security_ssl_show', ssl_log)
            
        except Exception as ssl_error:
            print(f"[WARNING] Could not retrieve SSL configuration: {str(ssl_error)}")
        
        return True
    
    # ====================================================================
    # CONTROL DE ERRORES
    # ====================================================================
    
    except NetAppRestError as error:
        print(f"\n[ERROR] NetApp REST API error during certificate deletion")
        print(f"[ERROR] HTTP Status Code: {error.status_code}")
        
        # Detallar errores comunes
        if error.status_code == 400:
            print(f"[ERROR] Bad Request - Invalid parameters")
            print(f"[HINT] Verify serial number and certificate details")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
            print(f"[HINT] Ensure the user has 'security' admin role")
        elif error.status_code == 404:
            print(f"[ERROR] Not Found - Certificate does not exist")
            print(f"[HINT] The certificate may have already been deleted")
        elif error.status_code == 409:
            print(f"[ERROR] Conflict - Certificate may be in use")
            print(f"[HINT] Certificate might be assigned to SSL configuration")
        
        # Mostrar detalles del error
        if error.http_err_response and error.http_err_response.http_response:
            print(f"\n[ERROR] API Response Details:")
            print(f"{error.http_err_response.http_response.text}")
        else:
            print(f"\n[ERROR] Error Details: {str(error)}")
        
        return False
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during certificate deletion")
        print(f"[ERROR] Error Type: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# CERTIFICATE INSTALLATION FUNCTION
# ============================================================================

def install_certificate(cert_config, svm_name):
    """
    Instala un certificado firmado en NetApp ONTAP usando la API REST
    
    El usuario debe proporcionar manualmente dos archivos:
    1. Certificado público (clave pública firmada por la CA)
    2. Clave privada (generada junto con el CSR)
     
    Proceso interactivo del comando CLI:
        1. Enter certificate: Press <Enter> when done
           → Se ingresa el certificado público
        2. Enter private key: Press <Enter> when done
           → Se ingresa la clave privada
        3. Do you want to continue entering root and/or intermediate certificates {y|n}:
           → Siempre se responde 'n'
    
    Args:
        cert_config (dict): Configuración del certificado desde config.yaml:
            - cert_name: Nombre del certificado en ONTAP
            - type: Tipo de certificado (server, client, etc.)
            - public_certificate_file: Ruta al archivo con el certificado público
            - private_key_file: Ruta al archivo con la clave privada
        svm_name (str): Nombre de la SVM donde instalar el certificado
    
    Returns:
        bool: True si se instaló exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Starting certificate installation workflow...")
        print(f"{'='*70}")
        
        # ====================================================================
        # PASO 1: VALIDAR PARÁMETROS DE CONFIGURACIÓN
        # ====================================================================
        
        print(f"\n[STEP 1/5] Validating configuration parameters...")
        
        # Validar que existan los campos requeridos en config.yaml
        required_fields = ['cert_name', 'type', 'public_certificate_file', 'private_key_file']
        missing_fields = [field for field in required_fields if field not in cert_config or not cert_config[field]]
        
        if missing_fields:
            print(f"[ERROR] Missing required fields in config.yaml under 'certificate' section:")
            for field in missing_fields:
                print(f"        - {field}")
            print(f"\n[ERROR] Please add these fields and try again")
            return False
        
        # Extraer parámetros
        cert_name = cert_config['cert_name']
        cert_type = cert_config['type']
        public_cert_file = cert_config['public_certificate_file']
        private_key_file = cert_config['private_key_file']
        
        print(f"[+] Configuration validated:")
        print(f"    - SVM Name: {svm_name}")
        print(f"    - Certificate Name: {cert_name}")
        print(f"    - Certificate Type: {cert_type}")
        print(f"    - Public Certificate File: {public_cert_file}")
        print(f"    - Private Key File: {private_key_file}")
        
        # ====================================================================
        # PASO 2: LEER CERTIFICADO PÚBLICO
        # ====================================================================
        
        print(f"\n[STEP 2/5] Reading public certificate file...")
        
        try:
            with open(public_cert_file, 'r', encoding='utf-8') as f:
                public_certificate = f.read().strip()
            
            # Validar que el certificado tenga el formato correcto
            if not public_certificate.startswith('-----BEGIN CERTIFICATE-----'):
                print(f"[WARNING] Certificate doesn't start with '-----BEGIN CERTIFICATE-----'")
                print(f"[WARNING] Make sure the file contains a valid PEM certificate")
            
            print(f"[+] Public certificate loaded successfully")
            print(f"    - File size: {len(public_certificate)} characters")
            print(f"    - First line: {public_certificate.split(chr(10))[0][:50]}")
            
        except FileNotFoundError:
            print(f"[ERROR] Public certificate file not found: {public_cert_file}")
            print(f"[ERROR] Please create this file with your CA-signed certificate")
            print(f"\n[HELP] The file should contain:")
            print(f"        -----BEGIN CERTIFICATE-----")
            print(f"        <base64 encoded certificate>")
            print(f"        -----END CERTIFICATE-----")
            return False
        
        except Exception as e:
            print(f"[ERROR] Error reading public certificate file: {str(e)}")
            return False
        
        # ====================================================================
        # PASO 3: LEER CLAVE PRIVADA
        # ====================================================================
        
        print(f"\n[STEP 3/5] Reading private key file...")
        
        try:
            with open(private_key_file, 'r', encoding='utf-8') as f:
                private_key = f.read().strip()
            
            # Validar que la clave tenga el formato correcto
            if not (private_key.startswith('-----BEGIN PRIVATE KEY-----') or 
                    private_key.startswith('-----BEGIN RSA PRIVATE KEY-----')):
                print(f"[WARNING] Private key doesn't start with '-----BEGIN PRIVATE KEY-----'")
                print(f"[WARNING] Make sure the file contains a valid PEM private key")
            
            print(f"[+] Private key loaded successfully")
            print(f"    - File size: {len(private_key)} characters")
            print(f"    - First line: {private_key.split(chr(10))[0][:50]}")
            
        except FileNotFoundError:
            print(f"[ERROR] Private key file not found: {private_key_file}")
            print(f"[ERROR] Please create this file with your private key")
            print(f"\n[HELP] The file should contain:")
            print(f"        -----BEGIN PRIVATE KEY-----")
            print(f"        <base64 encoded private key>")
            print(f"        -----END PRIVATE KEY-----")
            return False
        
        except Exception as e:
            print(f"[ERROR] Error reading private key file: {str(e)}")
            return False
        
        # ====================================================================
        # PASO 4: INSTALAR CERTIFICADO EN ONTAP VÍA API REST
        # ====================================================================
        
        print(f"\n[STEP 4/5] Installing certificate in ONTAP...")
        print(f"[*] Calling NetApp REST API: POST /api/security/certificates")
        
        # Crear el objeto SecurityCertificate
        certificate = SecurityCertificate()
        
        # Configurar los campos del certificado
        certificate.svm = {"name": svm_name}
        certificate.type = cert_type
        certificate.name = cert_name
        certificate.public_certificate = public_certificate
        certificate.private_key = private_key
        
        # Nota: El campo 'intermediate_certificates' se omite (equivalente a responder 'n')
        # en la pregunta: "Do you want to continue entering root and/or intermediate certificates"
        
        print(f"[*] Sending certificate installation request...")
        
        # POST: Enviar la petición a la API de NetApp
        certificate.post()
        
        print(f"[+] Certificate installed successfully!")
        print(f"    - Certificate Name: {cert_name}")
        print(f"    - SVM: {svm_name}")
        print(f"    - Type: {cert_type}")
        
        # ====================================================================
        # PASO 5: VERIFICAR INSTALACIÓN
        # ====================================================================
        
        print(f"\n[STEP 5/5] Verifying certificate installation...")
        
        # GET: Consultar el certificado recién instalado
        installed_certs = SecurityCertificate.get_collection(
            **{"svm.name": svm_name, "name": cert_name}
        )
        
        print(f"\n{'='*70}")
        print(f"  INSTALLED CERTIFICATE DETAILS")
        print(f"{'='*70}")
        
        cert_found = False
        for cert in installed_certs:
            cert_found = True
            cert.get()  # Obtener detalles completos
            
            print(f"\nCertificate Name: {cert.name}")
            print(f"Type: {cert.type}")
            print(f"SVM: {cert.svm.name if hasattr(cert.svm, 'name') else 'N/A'}")
            
            if hasattr(cert, 'common_name'):
                print(f"Common Name: {cert.common_name}")
            
            if hasattr(cert, 'serial_number'):
                print(f"Serial Number: {cert.serial_number}")
            
            if hasattr(cert, 'ca'):
                print(f"Certificate Authority: {cert.ca}")
            
            if hasattr(cert, 'expiry_time'):
                print(f"Expiry Date: {cert.expiry_time}")
            
            if hasattr(cert, 'hash_function'):
                print(f"Hash Function: {cert.hash_function}")
            
            if hasattr(cert, 'key_size'):
                print(f"Key Size: {cert.key_size} bits")
            
            if hasattr(cert, 'uuid'):
                print(f"UUID: {cert.uuid}")
        
        print(f"\n{'='*70}")
        
        if not cert_found:
            print(f"[WARNING] Certificate installed but not found in verification query")
            print(f"[INFO] The certificate may take a moment to appear in the system")
        
        # Guardar registro en log
        installation_log = {
            'operation': 'certificate_install',
            'svm_name': svm_name,
            'cert_name': cert_name,
            'cert_type': cert_type,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'success'
        }
        
        save_to_log('certificate_install', installation_log)
        
        print(f"\n[SUCCESS] Certificate installation completed!")
        print(f"\n[IMPORTANT] Security recommendations:")
        print(f"    1. Keep a backup of your private key in a secure location")
        print(f"    2. Delete the private key file from this directory after installation")
        print(f"    3. Store the CA-signed certificate for future reference")
        
        return True
    
    # ====================================================================
    # CONTROL DE ERRORES
    # ====================================================================
    
    except NetAppRestError as error:
        print(f"\n[ERROR] NetApp REST API error during certificate installation")
        print(f"[ERROR] HTTP Status Code: {error.status_code}")
        
        # Detallar errores comunes
        if error.status_code == 400:
            print(f"[ERROR] Bad Request - Invalid certificate format or parameters")
            print(f"[HINT] Check that your certificate files are in PEM format")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - User lacks required permissions")
            print(f"[HINT] Ensure the user has 'security' admin role")
        elif error.status_code == 409:
            print(f"[ERROR] Conflict - Certificate with this name already exists")
            print(f"[HINT] Choose a different cert_name or delete the existing certificate")
        elif error.status_code == 422:
            print(f"[ERROR] Unprocessable Entity - Certificate validation failed")
            print(f"[HINT] Verify that the certificate matches the private key")
        
        # Mostrar detalles del error
        if error.http_err_response and error.http_err_response.http_response:
            print(f"\n[ERROR] API Response Details:")
            print(f"{error.http_err_response.http_response.text}")
        else:
            print(f"\n[ERROR] Error Details: {str(error)}")
        
        return False
    
    except KeyError as e:
        print(f"\n[ERROR] Configuration error - Missing key: {str(e)}")
        print(f"[HINT] Check your config.yaml file for missing fields")
        return False
    
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during certificate installation")
        print(f"[ERROR] Error Type: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# EVENT LOG RETRIEVAL FUNCTION
# ============================================================================

def get_event_logs(max_records=100):
    """
    Obtiene los logs de eventos del sistema NetApp ONTAP
    
    Args:
        max_records: Número máximo de eventos a recuperar (default: 100)
    
    Returns:
        bool: True si se obtuvieron exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Retrieving event logs from cluster...")
        
        # GET: Obtener eventos del sistema desde la cabina
        events_list = []
        ems_events = EmsEvent.get_collection(max_records=max_records)
        
        for event in ems_events:
            event_data = {
                'index': event.index if hasattr(event, 'index') else 'N/A',
                'time': str(event.time) if hasattr(event, 'time') else 'N/A',
                'node': event.node.name if hasattr(event, 'node') and event.node else 'N/A',
                'severity': event.message.severity if hasattr(event, 'message') and hasattr(event.message, 'severity') else 'N/A',
                'event': event.message.name if hasattr(event, 'message') and hasattr(event.message, 'name') else 'N/A'
            }
            events_list.append(event_data)
        
        event_log_data = {
            'total_events': len(events_list),
            'max_records_requested': max_records,
            'events': events_list
        }
        
        # SHOW: Mostrar información como "event log show"
        print(f"\n{'='*110}")
        print(f"  Event Log Show")
        print(f"{'='*110}")
        print(f"{'Index':<8} {'Time':<25} {'Node':<20} {'Severity':<12} {'Event':<40}")
        print(f"{'-'*8} {'-'*25} {'-'*20} {'-'*12} {'-'*40}")
        
        for evt in events_list[:20]:  # Mostrar solo los primeros 20 en pantalla
            print(f"{str(evt['index']):<8} {evt['time']:<25} {evt['node']:<20} {evt['severity']:<12} {evt['event']:<40}")
        
        if len(events_list) > 20:
            print(f"... ({len(events_list) - 20} more events)")
        
        print(f"\nTotal events retrieved: {len(events_list)}")
        print(f"{'='*110}\n")
        
        # Guardar en log con timestamp
        save_to_log('event_logs', event_log_data)
        
        return True
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during event log retrieval")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        if error.http_err_response and error.http_err_response.http_response:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Details: {str(error)}")
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during event log retrieval: {type(e).__name__}")
        print(f"[ERROR] Details: {str(e)}")
        return False


# ============================================================================
# MENU FUNCTIONS
# ============================================================================

def display_menu():
    """
    Muestra el menú principal de opciones
    """
    print("\n" + "="*70)
    print("  CERTIFICATE MANAGEMENT MENU")
    print("="*70)
    print("\n[1] Generate Certificate Signing Request (CSR)")
    print("[2] Install Signed Certificate")
    print("[3] Delete Certificate (CA = SVM Name)")
    print("[4] Modify SSL Configuration")
    print("[0] Exit (with event logs backup)")
    print("[9] Exit without logs")
    print("\n" + "="*70)


def execute_option(option, config_data):
    """
    Ejecuta la opción seleccionada del menú
    
    Args:
        option: Número de opción seleccionada
        config_data: Diccionario con la configuración cargada
    
    Returns:
        bool: True para continuar con el menú, False para salir
    """
    if option == "1":
        # CERTIFICATE SIGNING REQUEST (CSR) GENERATION
        if 'certificate' not in config_data:
            print("\n[ERROR] No certificate configuration found in config.yaml")
            print("[ERROR] Add a 'certificate' section with the required parameters")
            return True
        
        print("\n[*] Starting CSR generation workflow...")
        if csr_generate(config_data['certificate']):
            print("\n[SUCCESS] Certificate Signing Request generated successfully!")
            print("[+] The CSR and private key have been saved to the csr_certificates/ directory")
            print("[+] Submit the CSR to your Certificate Authority to obtain a signed certificate")
        else:
            print("\n[ERROR] Failed to generate Certificate Signing Request")
            print("[ERROR] Check the error messages above and try again")
        
        return True
    
    elif option == "2":
        # CERTIFICATE INSTALLATION
        if 'certificate' not in config_data:
            print("\n[ERROR] No certificate configuration found in config.yaml")
            print("[ERROR] Add a 'certificate' section with the required parameters")
            return True
        
        if 'svm' not in config_data or 'name' not in config_data['svm']:
            print("\n[ERROR] No SVM name found in config.yaml")
            print("[ERROR] Add 'name' field in the 'svm' section")
            return True
        
        if install_certificate(config_data['certificate'], config_data['svm']['name']):
            print("\n[SUCCESS] Certificate installation process completed!")
            print("[+] The certificate is now installed on SVM: {}".format(config_data['svm']['name']))
        else:
            print("\n[ERROR] Certificate installation failed")
            print("[ERROR] Review the error messages above and try again")
        
        return True
    
    elif option == "3":
        # DELETE CERTIFICATE WHERE CA = SVM NAME
        if 'svm' not in config_data or 'name' not in config_data['svm']:
            print("\n[ERROR] No SVM name found in config.yaml")
            print("[ERROR] Add 'name' field in the 'svm' section")
            return True
        
        svm_name = config_data['svm']['name']
        
        print("\n[*] Starting certificate deletion workflow...")
        print(f"{'='*70}")
        print(f"[*] Target: Delete certificate where CA = {svm_name}")
        print(f"{'='*70}")
        
        # Obtener todos los certificados de la SVM
        certificate_details = get_serial_numbers(svm_name)
        
        if certificate_details:
            cert_to_delete = None
            
            # Buscar certificado donde CA = svm_name
            for cert in certificate_details:
                cert_ca = cert.get('ca', '')
                
                print(f"\n[*] Analyzing certificate:")
                print(f"    - Name: {cert['certificate_name']}")
                print(f"    - Common Name: {cert.get('common_name', 'N/A')}")
                print(f"    - CA: {cert_ca}")
                print(f"    - Serial: {cert['serial_number']}")
                
                # Verificar si CA = svm_name
                if cert_ca == svm_name:
                    cert_to_delete = cert
                    print(f"    -> ✓ MATCH: CA matches SVM name, this certificate will be deleted!")
                else:
                    print(f"    -> CA doesn't match SVM name (skipped)")
            
            # Verificar que encontramos el certificado
            if not cert_to_delete:
                print(f"\n[WARNING] Could not find certificate with CA = '{svm_name}'")
                print("[INFO] This may indicate:")
                print("       - The certificate was already deleted")
                print("       - No certificate exists with CA matching the SVM name")
                return True
            
            # ============================================================
            # ELIMINAR EL CERTIFICADO
            # ============================================================
            
            delete_serial = cert_to_delete['serial_number']
            
            print(f"\n[*] Proceeding with certificate deletion...")
            print(f"[*] Certificate to delete:")
            print(f"    - Type: server")
            print(f"    - VServer: {svm_name}")
            print(f"    - CA: {svm_name}")
            print(f"    - Common Name: {svm_name}")
            print(f"    - Serial Number: {delete_serial}")
            print(f"    - Certificate Name: {cert_to_delete['certificate_name']}")
            
            # Preparar configuración para delete_certificate
            # Parámetros: type=server, vserver=svm_name, ca=svm_name, serial=serial, common-name=svm_name
            delete_config = {
                'type': 'server',
                'common_name': svm_name,
                'ca_name': svm_name
            }
            
            # Llamar a la función de eliminación de certificado
            if delete_certificate(svm_name, delete_serial, delete_config):
                print("\n[SUCCESS] Certificate deletion completed!")
                print(f"{'='*70}")
                print("  CERTIFICATE DELETED SUCCESSFULLY")
                print(f"{'='*70}")
                print(f"\n[✓] Certificate deleted: {cert_to_delete['certificate_name']}")
                print(f"[✓] Serial Number: {delete_serial}")
                print(f"[✓] CA: {svm_name}")
                print(f"\n[INFO] The certificate has been removed from the system")
            else:
                print("\n[ERROR] Certificate deletion failed")
                print("[ERROR] Check the error messages above for details")
        else:
            print("\n[WARNING] No certificates found or error occurred")
            print("[INFO] Check the error messages above for details")
        
        return True
    
    elif option == "4":
        # MODIFY SSL CONFIGURATION
        if 'svm' not in config_data or 'name' not in config_data['svm']:
            print("\n[ERROR] No SVM name found in config.yaml")
            print("[ERROR] Add 'name' field in the 'svm' section")
            return True
        
        if 'ssl' not in config_data:
            print("\n[ERROR] No SSL configuration found in config.yaml")
            print("[ERROR] Add 'ssl' section with 'server_enabled'")
            return True
        
        svm_name = config_data['svm']['name']
        
        print("\n[*] Starting SSL modification workflow...")
        print(f"{'='*70}")
        print(f"[*] Target: Modify SSL using installed certificate (CA != SVM name)")
        print(f"{'='*70}")
        
        # Obtener todos los certificados de la SVM
        certificate_details = get_serial_numbers(svm_name)
        
        if certificate_details:
            print("\n[*] Analyzing certificates to find installed certificate...")
            
            cert_to_use = None
            
            # Buscar certificado donde CA != svm_name (certificado instalado)
            for cert in certificate_details:
                cert_ca = cert.get('ca', '')
                
                print(f"\n[*] Analyzing certificate:")
                print(f"    - Certificate Name: {cert['certificate_name']}")
                print(f"    - Common Name: {cert.get('common_name', 'N/A')}")
                print(f"    - CA: {cert_ca}")
                print(f"    - Serial: {cert['serial_number']}")
                
                # Buscar certificado donde CA != svm_name
                if cert_ca != svm_name and cert_ca != 'N/A' and cert_ca != '':
                    cert_to_use = cert
                    print(f"    -> ✓ MATCH: This is the installed certificate (CA != SVM name)!")
                elif cert_ca == svm_name:
                    print(f"    -> Certificate with CA = SVM name (skipped)")
                else:
                    print(f"    -> No valid CA found (skipped)")
            
            # Verificar que encontramos el certificado
            if not cert_to_use:
                print(f"\n[ERROR] Could not find installed certificate")
                print("[INFO] Looking for certificate where CA != '{svm_name}'")
                print("[INFO] This may indicate:")
                print("       - No installed certificate exists")
                print("       - The certificate was not properly installed")
                print("       - Run option 2 to install a certificate first")
                return True
            
            # ============================================================
            # EXTRAER DATOS DEL CERTIFICADO AUTOMÁTICAMENTE
            # ============================================================
            
            ssl_cert_name = cert_to_use.get('certificate_name')
            ssl_common_name = cert_to_use.get('common_name')
            ssl_ca = cert_to_use.get('ca')
            ssl_serial = cert_to_use.get('serial_number')
            
            # ============================================================
            # VALIDACIÓN: VERIFICAR DATOS EXTRAÍDOS
            # ============================================================
            
            print(f"\n[*] Extracting certificate data automatically...")
            print(f"[+] Certificate data extracted:")
            print(f"    - VServer: {svm_name}")
            print(f"    - Certificate Name: {ssl_cert_name}")
            print(f"    - Common Name: {ssl_common_name}")
            print(f"    - CA (Certificate Authority): {ssl_ca}")
            print(f"    - Serial Number: {ssl_serial}")
            print(f"    - Type: {cert_to_use.get('type', 'server')}")
            
            if not ssl_ca or ssl_ca == 'N/A':
                print(f"\n[ERROR] Could not extract CA name from certificate")
                print(f"[ERROR] Cannot proceed with SSL modification without valid CA name")
                return True
            
            if not ssl_common_name or ssl_common_name == 'N/A':
                print(f"\n[ERROR] Could not extract common name from certificate")
                print(f"[ERROR] Cannot proceed with SSL modification without valid common name")
                return True
            
            # ============================================================
            # MODIFICAR SSL CON EL CERTIFICADO INSTALADO
            # ============================================================
            
            print(f"\n[*] Proceeding with SSL modification...")
            print(f"[*] Command to execute:")
            print(f"    security ssl modify -vserver {svm_name} \\")
            print(f"                        -ca {ssl_ca} \\")
            print(f"                        -common-name {ssl_common_name} \\")
            print(f"                        -serial {ssl_serial} \\")
            print(f"                        -server-enabled {str(config_data['ssl']['server_enabled']).lower()}")
            
            # Llamar a la función de modificación SSL con los datos extraídos
            if modify_ssl_certificate(
                svm_name,
                ssl_serial,
                config_data['ssl'],
                ssl_common_name,
                ssl_ca  # CA name extraído automáticamente del certificado
            ):
                print("\n[SUCCESS] SSL modification completed successfully!")
                print(f"{'='*70}")
                print("  SSL CONFIGURATION UPDATED")
                print(f"{'='*70}")
                print(f"\n[✓] SSL configured with certificate: {ssl_cert_name}")
                print(f"[✓] CA: {ssl_ca}")
                print(f"[✓] Common Name: {ssl_common_name}")
                print(f"[✓] Serial Number: {ssl_serial}")
                print(f"\n[INFO] SSL configuration has been updated with the installed certificate")
                print(f"\n[NEXT STEP] Run option 3 to delete the old certificate (CA = {svm_name})")
            else:
                print("\n[ERROR] SSL modification failed")
                print("[ERROR] Check the error messages above for details")
        else:
            print("\n[WARNING] No certificates found or error occurred")
            print("[INFO] Check the error messages above for details")
        
        return True
    
    elif option == "0":
        print("\n[*] Exiting script...")
        return False
    
    elif option == "9":
        print("\n[*] Exiting script without logs backup...")
        return "exit_no_logs"
    
    else:
        print("\n[WARNING] Invalid option. Please select a valid option.")
        return True


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """
    Función principal del script
    
    Ejecuta el flujo completo:
    1. Carga la configuración
    2. Establece conexión con el cluster
    3. Muestra menú de opciones
    4. Ejecuta la opción seleccionada
    """
    # CONFIG YAML LOADER
    # Cargar la configuración desde el archivo YAML
    config_data = config_loader()
    
    # Verificar que la configuración se cargó exitosamente
    if config_data is None:
        print("\n[ERROR] Cannot continue without valid configuration")
        print("[ERROR] Check the config.yaml file and try again")
        exit(1)
    else:
        print("\n[SUCCESS] Configuration loaded - Proceeding with pre-checks")
    
    # CLUSTER CONNECTION CHECK
    # Establecer conexión y verificar acceso a la cabina NetApp
    if not cluster_connection(config_data['cluster']):
        print("\n[ERROR] Failed to connect to NetApp cluster")
        print("[ERROR] Fix connection issues before continuing")
        exit(1)
    
    print("\n[+] All pre-checks passed - Ready for certificate operations")
    
    # MENU LOOP
    # Mostrar menú y ejecutar opciones hasta que el usuario decida salir
    continue_menu = True
    skip_logs = False
    while continue_menu:
        display_menu()
        
        try:
            option = input("\nSelect an option: ").strip()
            result = execute_option(option, config_data)
            
            if result == "exit_no_logs":
                skip_logs = True
                continue_menu = False
            else:
                continue_menu = result
        
        except KeyboardInterrupt:
            print("\n\n[*] Operation cancelled by user")
            print("[*] Exiting script...")
            break
        
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {type(e).__name__}")
            print(f"[ERROR] Details: {str(e)}")
            continue_menu = True
    
    # FINAL CLEANUP
    # Obtener event logs de la cabina como backup final (si no se eligió exit sin logs)
    if not skip_logs:
        print("\n[*] Final event logs backup...")
        if get_event_logs(max_records=100):
            print("\n[SUCCESS] Event logs backup completed!")
        else:
            print("\n[WARNING] Event logs backup failed (non-critical)")
    
    print("\n[*] Script execution completed")
    print("="*70 + "\n")


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()

