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
    
    Ejemplo:
        save_to_log('create_svm', svm_data)
        # Crea: logs/create_svm_20260129_143025.json
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
            
            # DEBUG: Mostrar las claves disponibles en la respuesta
            print(f"[DEBUG] Response keys: {list(response_data.keys())}")
            
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
                    print(f"[DEBUG] Found CSR in field: {key}")
                    break
            
            # Buscar la clave privada en diferentes posibles nombres de campo
            private_key_content = None
            for key in ['generated_private_key', 'private_key', 'key', 'privateKey']:
                if key in response_data:
                    private_key_content = response_data[key]
                    print(f"[DEBUG] Found private key in field: {key}")
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
# CERTIFICATE MODIFICATION FUNCTION
# ============================================================================

def modify_certificate(svm_name, cert_config=None):
    """
    Modifica certificados en NetApp ONTAP
    
    Equivalente a:
    security certificate show -vserver <svm> -instance
    security ssl modify -vserver <svm> -common-name <cn> -serial <serial1> -server-enabled true/false
    security certificate delete -type server -vserver <svm> -serial <serial2> -common-name <cn>
    security ssl show -vserver <svm>
    
    Muestra los certificados de una SVM, filtra los que tienen common_name
    y certificate_name, extrae los Serial Numbers, y realiza operaciones:
    - Primer certificado: Habilita/Deshabilita SSL según config (security ssl modify)
    - Segundo certificado: Elimina el certificado (security certificate delete)
    - Muestra la configuración SSL final
    
    Args:
        svm_name: Nombre de la SVM para filtrar certificados
        cert_config: Diccionario con configuración (opcional, incluye ssl_enabled)
    
    Returns:
        bool: True si se ejecutó exitosamente, False si hubo error
    """
    try:
        print(f"\n[*] Starting certificate modification workflow...")
        print(f"[*] Retrieving certificates for SVM: {svm_name}")
        
        # GET: Obtener certificados filtrando por SVM
        print(f"\n[*] Calling NetApp API to retrieve certificates...")
        
        certificates = SecurityCertificate.get_collection(
            **{"svm.name": svm_name}
        )
        
        print(f"\n{'='*110}")
        print(f"  Certificate Show - SVM: {svm_name}")
        print(f"{'='*110}\n")
        
        # Lista para almacenar certificados con sus datos
        certificate_data = []
        cert_count = 0
        
        for cert in certificates:
            # Obtener detalles completos del certificado
            cert.get()
            
            # Verificar si tiene common_name y name (certificate_name)
            has_common_name = hasattr(cert, 'common_name') and cert.common_name
            has_cert_name = hasattr(cert, 'name') and cert.name
            
            # Solo procesar certificados que tengan ambos campos
            if has_common_name and has_cert_name:
                cert_count += 1
                
                print(f"Certificate #{cert_count}:")
                print(f"{'-'*110}")
                print(f"Certificate Name: {cert.name}")
                print(f"Common Name: {cert.common_name}")
                
                # Almacenar datos del certificado
                cert_info = {
                    'name': cert.name,
                    'common_name': cert.common_name,
                    'serial_number': None,
                    'uuid': cert.uuid if hasattr(cert, 'uuid') else None
                }
                
                # Extraer Serial Number si existe
                if hasattr(cert, 'serial_number') and cert.serial_number:
                    cert_info['serial_number'] = cert.serial_number
                    print(f"Serial Number: {cert.serial_number}")
                else:
                    print(f"Serial Number: N/A")
                
                # Mostrar información adicional
                if hasattr(cert, 'type'):
                    cert_info['type'] = cert.type
                    print(f"Type: {cert.type}")
                
                if hasattr(cert, 'ca'):
                    print(f"CA: {cert.ca}")
                
                if hasattr(cert, 'expiry_time'):
                    print(f"Expiry Time: {cert.expiry_time}")
                
                if hasattr(cert, 'hash_function'):
                    print(f"Hash Function: {cert.hash_function}")
                
                if hasattr(cert, 'key_size'):
                    print(f"Key Size: {cert.key_size} bits")
                
                certificate_data.append(cert_info)
                print(f"")
        
        print(f"{'='*110}")
        print(f"\nTotal certificates found with Common Name and Certificate Name: {cert_count}")
        
        # Imprimir resumen de Serial Numbers
        serial_numbers = [cert['serial_number'] for cert in certificate_data if cert['serial_number']]
        if serial_numbers:
            print(f"\n[+] Serial Numbers extracted:")
            for idx, serial in enumerate(serial_numbers, 1):
                print(f"    [{idx}] {serial}")
            
            # EXECUTE SSL MODIFY WITH FIRST SERIAL NUMBER
            if len(serial_numbers) > 0:
                print(f"\n[*] Executing SSL modify with first serial number...")
                first_serial = serial_numbers[0]
                
                # Get SSL configuration from cert_config
                ssl_config = cert_config.get('ssl', {}) if cert_config else {}
                ca_name = ssl_config.get('ca_name', 'vdc-ca')
                # Use common_name from certificate section, fallback to first certificate's common_name
                common_name = cert_config.get('common_name', certificate_data[0]['common_name']) if cert_config else certificate_data[0]['common_name']
                server_enabled = ssl_config.get('server_enabled', True)
                
                print(f"[+] SSL Modify Parameters:")
                print(f"    - VServer: {svm_name}")
                print(f"    - CA: {ca_name}")
                print(f"    - Common Name: {common_name}")
                print(f"    - Serial Number: {first_serial}")
                print(f"    - Server Enabled: {server_enabled}")
                
                try:
                    # Execute SSL modify using ONTAP REST API
                    # The equivalent to: security ssl modify -vserver <vserver> -ca <ca> -common-name <cn> -serial <serial> -server-enabled true
                    from netapp_ontap.resources import SecurityCertificate
                    
                    # Build the query to find the certificate
                    cert_to_modify = SecurityCertificate.find(
                        **{
                            "svm.name": svm_name,
                            "serial_number": first_serial,
                            "common_name": common_name
                        }
                    )
                    
                    if cert_to_modify:
                        print(f"[+] Certificate found - UUID: {cert_to_modify.uuid}")
                        
                        # Note: The security ssl modify command is typically done via CLI
                        # For REST API, we'll construct the command and show it
                        ssl_modify_cmd = (
                            f"security ssl modify "
                            f"-vserver {svm_name} "
                            f"-ca {ca_name} "
                            f"-common-name {common_name} "
                            f"-serial {first_serial} "
                            f"-server-enabled {str(server_enabled).lower()}"
                        )
                        
                        print(f"\n[+] CLI Command to execute:")
                        print(f"    {ssl_modify_cmd}")
                        
                        # Save command to log
                        ssl_modify_data = {
                            'command': ssl_modify_cmd,
                            'vserver': svm_name,
                            'ca': ca_name,
                            'common_name': common_name,
                            'serial_number': first_serial,
                            'server_enabled': server_enabled,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_to_log('ssl_modify_command', ssl_modify_data)
                        
                        print(f"[SUCCESS] SSL modify command generated and saved to logs")
                    else:
                        print(f"[WARNING] Certificate not found for modification")
                        
                except Exception as ssl_error:
                    print(f"[ERROR] Error during SSL modify: {type(ssl_error).__name__}")
                    print(f"[ERROR] Details: {str(ssl_error)}")
                
                # SHOW SSL CONFIGURATION
                print(f"\n[*] Retrieving SSL configuration for verification...")
                try:
                    # The equivalent to: security ssl show -vserver <vserver>
                    ssl_show_cmd = f"security ssl show -vserver {svm_name}"
                    
                    print(f"\n{'='*110}")
                    print(f"  SSL Configuration - VServer: {svm_name}")
                    print(f"{'='*110}")
                    print(f"\n[+] CLI Command to view SSL configuration:")
                    print(f"    {ssl_show_cmd}")
                    
                    # Query certificates with SSL role
                    ssl_certs = SecurityCertificate.get_collection(
                        **{"svm.name": svm_name, "type": "server"}
                    )
                    
                    ssl_count = 0
                    for ssl_cert in ssl_certs:
                        ssl_cert.get()
                        ssl_count += 1
                        
                        print(f"\n[{ssl_count}] SSL Certificate:")
                        print(f"    Name: {ssl_cert.name if hasattr(ssl_cert, 'name') else 'N/A'}")
                        print(f"    Common Name: {ssl_cert.common_name if hasattr(ssl_cert, 'common_name') else 'N/A'}")
                        print(f"    Serial Number: {ssl_cert.serial_number if hasattr(ssl_cert, 'serial_number') else 'N/A'}")
                        print(f"    CA: {ssl_cert.ca if hasattr(ssl_cert, 'ca') else 'N/A'}")
                        print(f"    Expiry: {ssl_cert.expiry_time if hasattr(ssl_cert, 'expiry_time') else 'N/A'}")
                    
                    print(f"\n{'='*110}")
                    print(f"[INFO] Total SSL certificates found: {ssl_count}")
                    
                except Exception as show_error:
                    print(f"[WARNING] Could not retrieve SSL configuration: {str(show_error)}")
                    
        else:
            print(f"\n[WARNING] No serial numbers found in the certificates")
            return False
    
    # CONTROL DE ERRORES
    except NetAppRestError as error:
        print(f"[ERROR] NetApp API error during certificate modification")
        print(f"[ERROR] HTTP Status: {error.status_code}")
        
        if error.status_code == 400:
            print(f"[ERROR] Bad request - Check SVM name and parameters")
        elif error.status_code == 403:
            print(f"[ERROR] Forbidden - Insufficient permissions")
        elif error.status_code == 404:
            print(f"[ERROR] Not found - SVM or certificate may not exist")
        
        if error.http_err_response and error.http_err_response.http_response:
            print(f"[ERROR] Details: {error.http_err_response.http_response.text}")
        else:
            print(f"[ERROR] Details: {str(error)}")
        
        return False
    
    except Exception as e:
        print(f"[ERROR] Unexpected error during certificate modification: {type(e).__name__}")
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
    print("[3] Modify Certificate (Show & Extract Serial Numbers)")
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
    
    elif option == "3":
        # CERTIFICATE MODIFICATION
        if 'svm' not in config_data or 'name' not in config_data['svm']:
            print("\n[ERROR] No SVM name found in config.yaml")
            print("[ERROR] Add 'name' field in 'svm' section")
            return True
        
        # Combinar configuración de certificado y SSL
        cert_config = {}
        if 'certificate' in config_data:
            cert_config.update(config_data['certificate'])
        if 'ssl' in config_data:
            cert_config['ssl'] = config_data['ssl']
        
        print("\n[*] Starting certificate modification workflow...")
        if modify_certificate(config_data['svm']['name'], cert_config):
            print("\n[SUCCESS] Certificate modification completed successfully!")
            print("[+] SSL modify command generated and saved")
        else:
            print("\n[ERROR] Failed to modify certificates")
            print("[ERROR] Check the error messages above and try again")
        
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

