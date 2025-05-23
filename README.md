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

