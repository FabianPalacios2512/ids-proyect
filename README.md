# Proyecto-ids

# IDS_Proyecto - Sistema de Detección de Intrusos en Red

Este proyecto es un **IDS (Intrusion Detection System)** desarrollado en Python con Flask, orientado a la detección de comportamientos sospechosos en una red. El sistema permite capturar, analizar y registrar eventos potencialmente maliciosos, y además ofrece una **interfaz web** para la gestión de usuarios y visualización de eventos.

---

## 🚀 ¿Qué hace este sistema?

- Captura paquetes de red en tiempo real utilizando **Scapy**.
- Aplica reglas personalizadas para identificar actividades sospechosas (por ejemplo: accesos a puertos restringidos, TTL anómalos, flood SYN).
- Registra eventos en una base de datos **MariaDB/MySQL**.
- Bloquea temporalmente usuarios tras intentos fallidos de inicio de sesión mediante **Redis**.
- Ofrece una interfaz web desarrollada con **Flask**, HTML y TailwindCSS para gestión de usuarios, eventos e informes.

---

## ⚙️ Tecnologías utilizadas

- Python 3.13
- Flask 3.1
- Scapy
- MariaDB / MySQL
- Redis (para control de acceso y bloqueo temporal)
- HTML, JavaScript y TailwindCSS

---

## 🧱 Estructura del Proyecto

IDS_Proyecto/
│
├── app.py # Arranque principal del servidor Flask
├── controlador/ # Controladores de login, usuarios, etc.
├── modelo/ # Lógica de acceso a base de datos
├── vistas/ # HTML y diseño de la interfaz
├── static/ # Archivos estáticos (JS, CSS, imágenes)
├── analizador/ # Módulo de escaneo y análisis de paquetes
├── requirements.txt # Dependencias necesarias
├── README.md 




---

## 🛠️ Instalación del entorno

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu_usuario/IDS_Proyecto.git
cd IDS_Proyecto


2. Crear entorno virtual
python3.13 -m venv venv
source venv/bin/activate


3. Instalar dependencias
pip install -r requirements.txt


4. Instalar y activar Redis
En Kali Linux o Debian:

sudo apt update
sudo apt install redis-server











