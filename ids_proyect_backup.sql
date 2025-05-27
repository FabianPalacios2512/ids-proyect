/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.1-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: ids_proyect
-- ------------------------------------------------------
-- Server version	11.8.1-MariaDB-4

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `dispositivos`
--

DROP TABLE IF EXISTS `dispositivos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `dispositivos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `direccion_ip` varchar(45) NOT NULL,
  `direccion_mac` varchar(20) DEFAULT NULL,
  `nombre_host` varchar(255) DEFAULT NULL,
  `sistema_operativo` varchar(255) DEFAULT NULL,
  `puerto` text DEFAULT NULL,
  `fecha_escaneo` timestamp NULL DEFAULT current_timestamp(),
  `estado_dispositivo` varchar(20) DEFAULT 'activo',
  `bloqueado` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dispositivos`
--

LOCK TABLES `dispositivos` WRITE;
/*!40000 ALTER TABLE `dispositivos` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `dispositivos` VALUES
(1,'192.168.0.1','98:F7:81:A9:D2:5F','','Linux 2.6.39','5000','2025-05-27 15:35:24','activo',0),
(2,'192.168.0.253','00:00:CA:01:02:03','','Desconocido','','2025-05-27 15:45:10','activo',0),
(3,'192.168.0.3','8E:23:64:F6:D4:22','','Desconocido','','2025-05-27 02:41:47','inactivo',0),
(4,'192.168.0.7','Desconocido','','Linux 2.6.32','902','2025-05-26 23:37:23','activo',0),
(5,'192.168.0.9','D6:39:36:A7:15:35','','Apple macOS 11 (Big Sur) - 13 (Ventura) or iOS 16 (Darwin 20.6.0 - 22.4.0)','49152, 62078','2025-05-25 21:26:46','inactivo',0),
(6,'192.168.0.1','98:F7:81:A9:D2:5F','','Desconocido','','2025-05-27 15:45:10','activo',0),
(7,'192.168.0.11','2E:A3:B3:3A:CA:1A','','Desconocido','','2025-05-27 02:41:47','inactivo',0),
(8,'192.168.0.2','F2:3A:6C:1E:89:42','','Desconocido','','2025-05-27 15:45:10','activo',0),
(9,'192.168.0.4','08:00:27:B4:A1:05','','Desconocido','','2025-05-26 19:38:18','inactivo',0),
(10,'192.168.0.5','A2:16:41:B2:0A:31','','Desconocido','','2025-05-27 02:41:47','inactivo',0),
(11,'192.168.0.7','Desconocido','','Linux 2.6.32','902, 7070','2025-05-27 15:45:10','activo',0);
/*!40000 ALTER TABLE `dispositivos` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `escanear_red`
--

DROP TABLE IF EXISTS `escanear_red`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `escanear_red` (
  `idescanear_red` int(11) NOT NULL AUTO_INCREMENT,
  `iporigen` varchar(45) NOT NULL,
  `ipdestino` varchar(45) NOT NULL,
  `mac_origen` varchar(45) DEFAULT NULL,
  `mac_destino` varchar(45) DEFAULT NULL,
  `puerto_origen` smallint(5) unsigned DEFAULT NULL,
  `puerto_destino` smallint(5) unsigned DEFAULT NULL,
  `protocolo` varchar(45) DEFAULT NULL,
  `tamano` int(11) DEFAULT NULL,
  `fecha_captura` timestamp NULL DEFAULT current_timestamp(),
  `ttl` int(11) DEFAULT NULL,
  `flags_tcp` varchar(15) DEFAULT NULL,
  `payload` text DEFAULT NULL,
  `protocolo_nombre` varchar(50) DEFAULT NULL,
  `descripcion_flags` varchar(100) DEFAULT NULL,
  `descripcion_payload` text DEFAULT NULL,
  PRIMARY KEY (`idescanear_red`),
  KEY `idx_iporigen` (`iporigen`),
  KEY `idx_ipdestino` (`ipdestino`),
  KEY `idx_protocolo` (`protocolo`),
  KEY `idx_fecha_captura` (`fecha_captura`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `escanear_red`
--

LOCK TABLES `escanear_red` WRITE;
/*!40000 ALTER TABLE `escanear_red` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `escanear_red` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `eventos`
--

DROP TABLE IF EXISTS `eventos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eventos` (
  `id_evento` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_evento` varchar(50) NOT NULL,
  `descripcion` text NOT NULL,
  `usuario` varchar(100) DEFAULT NULL,
  `fecha_evento` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_evento`)
) ENGINE=InnoDB AUTO_INCREMENT=298 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eventos`
--

LOCK TABLES `eventos` WRITE;
/*!40000 ALTER TABLE `eventos` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `eventos` VALUES
(1,'Cierre de sesión','Logout','Juan','2025-04-10 01:29:23'),
(2,'Acción del sistema','Inicio de sesión','Juan','2025-04-10 01:29:26'),
(3,'Actualizó al usuario con ID: 3','Actualización de usuario','Juan','2025-04-10 01:32:25'),
(4,'Actualización de perfil','Se actualizó el perfil con ID 4 (Nombre: YA FUNCIONA, Estado: activo)','Juan','2025-04-10 01:32:45'),
(5,'Cierre de sesión','Logout','Juan','2025-04-10 01:36:39'),
(6,'Acción del sistema','Inicio de sesión','Fabian','2025-04-10 01:36:46'),
(7,'Cierre de sesión','Logout','Fabian','2025-04-10 01:52:21'),
(8,'Acción del sistema','Inicio de sesión','Fabian','2025-04-10 01:52:26'),
(9,'Acción del sistema','Inicio de sesión','Fabian','2025-04-11 00:15:57'),
(10,'captura_paquetes','Inició la captura de paquetes',NULL,'2025-04-11 02:14:12'),
(11,'captura_paquetes','Inició la captura de paquetes',NULL,'2025-04-11 02:15:49'),
(12,'captura_paquetes','Inició la captura de paquetes',NULL,'2025-04-11 02:17:03'),
(13,'captura_paquetes','Inició la captura de paquetes',NULL,'2025-04-11 02:39:06'),
(14,'Acción del sistema','Inicio de sesión','Fabian','2025-04-11 11:34:15'),
(15,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 02:59:11'),
(16,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 11:06:39'),
(17,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 12:54:02'),
(18,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 13:04:05'),
(19,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 13:08:47'),
(20,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 13:25:24'),
(21,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 13:38:33'),
(22,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 14:08:30'),
(23,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 14:21:49'),
(24,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 14:33:58'),
(25,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 17:03:47'),
(26,'Acción del sistema','Inicio de sesión','Fabian','2025-04-12 19:29:20'),
(27,'Acción del sistema','Inicio de sesión','Fabian','2025-04-13 12:51:02'),
(28,'Acción del sistema','Inicio de sesión','Fabian','2025-04-13 13:03:03'),
(29,'Acción del sistema','Inicio de sesión','Fabian','2025-04-13 18:44:02'),
(30,'Acción del sistema','Inicio de sesión','Fabian','2025-04-13 18:54:42'),
(31,'Se creó el perfil: Juan','Creación de perfil','Fabian','2025-04-13 19:13:17'),
(32,'Actualización de perfil','Se actualizó el perfil con ID 6 (Nombre: Juan, Estado: activo)','Fabian','2025-04-13 19:13:25'),
(33,'Acción del sistema','Inicio de sesión','Fabian','2025-04-13 21:10:13'),
(34,'Se inhabilitó el perfil con ID 4','Inhabilitación de perfil','Fabian','2025-04-13 23:07:52'),
(35,'Acción del sistema','Inicio de sesión','Fabian','2025-04-13 23:44:09'),
(36,'Acción del sistema','Inicio de sesión','Fabian','2025-04-14 00:47:43'),
(37,'Acción del sistema','Inicio de sesión','Fabian','2025-04-14 18:58:53'),
(38,'Acción del sistema','Inicio de sesión','Fabian','2025-04-14 19:28:08'),
(39,'Acción del sistema','Inicio de sesión','Fabian','2025-04-15 12:41:56'),
(40,'Acción del sistema','Inicio de sesión','Fabian','2025-04-15 13:35:35'),
(41,'Acción del sistema','Inicio de sesión','Fabian','2025-04-15 17:15:26'),
(42,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 11:20:18'),
(43,'Cierre de sesión','Logout','Fabian','2025-04-25 11:24:40'),
(44,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 11:24:46'),
(45,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 11:55:37'),
(46,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 12:17:54'),
(47,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 13:13:23'),
(48,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 21:33:37'),
(49,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 21:33:38'),
(50,'Acción del sistema','Inicio de sesión','Fabian','2025-04-25 22:27:46'),
(51,'Acción del sistema','Inicio de sesión','Fabian','2025-04-26 15:48:06'),
(52,'Acción del sistema','Inicio de sesión','Fabian','2025-04-30 11:44:52'),
(53,'Acción del sistema','Inicio de sesión','Fabian','2025-04-30 23:22:49'),
(54,'Cierre de sesión','Logout','Fabian','2025-04-30 23:23:10'),
(55,'Acción del sistema','Inicio de sesión','Fabian','2025-04-30 23:25:25'),
(56,'Acción del sistema','Inicio de sesión','Fabian','2025-05-02 21:17:31'),
(57,'Se inhabilitó el usuario con ID: 6','Eliminación de usuario','Fabian','2025-05-02 21:23:22'),
(58,'Acción del sistema','Inicio de sesión','Fabian','2025-05-02 21:24:28'),
(59,'Se creó el perfil: U NACIONAL','Creación de perfil','Fabian','2025-05-02 21:24:41'),
(60,'Actualización de perfil','Se actualizó el perfil con ID 1 (Nombre: Administrador, Estado: activo)','Fabian','2025-05-02 21:31:56'),
(61,'Actualización de perfil','Se actualizó el perfil con ID 1 (Nombre: Administrador, Estado: activo)','Fabian','2025-05-02 21:32:33'),
(62,'Actualización de perfil','Se actualizó el perfil con ID 2 (Nombre: Administrador, Estado: activo)','Fabian','2025-05-02 21:32:40'),
(63,'Actualizó al usuario con ID: 3','Actualización de usuario','Fabian','2025-05-02 21:36:45'),
(64,'Se inhabilitó el usuario con ID: 6','Eliminación de usuario','Fabian','2025-05-02 21:37:03'),
(65,'Se inhabilitó el perfil con ID 7','Inhabilitación de perfil','Fabian','2025-05-02 21:37:22'),
(66,'Se inhabilitó el perfil con ID 6','Inhabilitación de perfil','Fabian','2025-05-02 21:37:26'),
(67,'Se inhabilitó el perfil con ID 2','Inhabilitación de perfil','Fabian','2025-05-02 21:37:32'),
(68,'Se inhabilitó el perfil con ID 1','Inhabilitación de perfil','Fabian','2025-05-02 21:37:37'),
(69,'Se inhabilitó el perfil con ID 1','Inhabilitación de perfil','Fabian','2025-05-02 21:37:41'),
(70,'Actualización de perfil','Se actualizó el perfil con ID 1 (Nombre: Administrador, Estado: activo)','Fabian','2025-05-02 21:37:47'),
(71,'Actualización de perfil','Se actualizó el perfil con ID 2 (Nombre: cajero, Estado: activo)','Fabian','2025-05-02 21:38:03'),
(72,'Actualizó al usuario con ID: 3','Actualización de usuario','Fabian','2025-05-02 21:38:17'),
(73,'Se inhabilitó el usuario con ID: 3','Eliminación de usuario','Fabian','2025-05-02 21:38:24'),
(74,'Actualización de perfil','Se actualizó el perfil con ID 1 (Nombre: Administrador, Estado: activo)','Fabian','2025-05-02 21:51:46'),
(75,'Cierre de sesión','Logout','Fabian','2025-05-02 21:55:44'),
(76,'Acción del sistema','Inicio de sesión','NuevoAdmin','2025-05-02 21:59:02'),
(77,'Acción del sistema','Inicio de sesión','NuevoAdmin','2025-05-02 22:10:20'),
(78,'Se creó el usuario: Fabian Paterina','Creación de usuario','NuevoAdmin','2025-05-02 22:16:54'),
(79,'Se creó el perfil: Cliente','Creación de perfil','NuevoAdmin','2025-05-02 22:18:07'),
(80,'Se creó el usuario: Maria Jose  Gonzalez','Creación de usuario','NuevoAdmin','2025-05-02 22:19:54'),
(81,'Cierre de sesión','Logout','NuevoAdmin','2025-05-02 22:20:09'),
(82,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-02 22:20:19'),
(83,'Cierre de sesión','Logout','Maria Jose ','2025-05-02 22:38:56'),
(84,'Acción del sistema','Inicio de sesión','Fabian','2025-05-02 22:39:01'),
(85,'Cierre de sesión','Logout','Fabian','2025-05-02 22:48:13'),
(86,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-02 22:49:29'),
(87,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-02 23:55:00'),
(88,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 00:23:01'),
(89,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 01:42:04'),
(90,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 02:14:38'),
(91,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 02:20:45'),
(92,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 02:31:46'),
(93,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 02:37:58'),
(94,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 03:05:10'),
(95,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 03:14:24'),
(96,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 05:12:07'),
(97,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 10:58:36'),
(98,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 11:27:48'),
(99,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 11:54:13'),
(100,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 12:01:36'),
(101,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 12:26:14'),
(102,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 16:01:25'),
(103,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-03 16:53:10'),
(104,'Cierre de sesión','Logout','Maria Jose ','2025-05-03 17:38:32'),
(105,'Acción del sistema','Inicio de sesión','Fabian','2025-05-03 20:52:21'),
(106,'Acción del sistema','Inicio de sesión','Fabian','2025-05-03 21:06:03'),
(107,'Acción del sistema','Inicio de sesión','Fabian','2025-05-03 21:16:28'),
(108,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-03 21:27:23'),
(109,'Actualizó al usuario con ID: 11','Actualización de usuario','Fabian','2025-05-03 21:29:41'),
(110,'Actualizó al usuario con ID: 11','Actualización de usuario','Fabian','2025-05-03 21:31:17'),
(111,'Actualizó al usuario con ID: 11','Actualización de usuario','Fabian','2025-05-03 21:32:55'),
(112,'Cierre de sesión','Logout','Fabian','2025-05-03 21:35:00'),
(113,'Acción del sistema','Inicio de sesión','Fabian','2025-05-03 21:35:49'),
(114,'Se creó el usuario: Gloria Lora','Creación de usuario','Fabian','2025-05-03 21:37:51'),
(115,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-03 21:38:30'),
(116,'Se inhabilitó el usuario con ID: 10','Eliminación de usuario','Fabian','2025-05-03 21:38:49'),
(117,'Acción del sistema','Inicio de sesión','Fabian','2025-05-04 13:52:04'),
(118,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-04 13:52:30'),
(119,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-04 13:52:40'),
(120,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-04 13:52:46'),
(121,'Se inhabilitó el usuario con ID: 10','Eliminación de usuario','Fabian','2025-05-04 13:52:59'),
(122,'Actualizó al usuario con ID: 16','Actualización de usuario','Fabian','2025-05-04 13:53:12'),
(123,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-04 14:07:27'),
(124,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-04 14:37:22'),
(125,'Actualizó al usuario con ID: 10','Actualización de usuario','Fabian','2025-05-04 14:42:37'),
(126,'Se creó el usuario: Fabian PATERNINA','Creación de usuario','Fabian','2025-05-04 14:43:12'),
(127,'Actualizó al usuario con ID: 11','Actualización de usuario','Fabian','2025-05-04 14:43:37'),
(128,'Cierre de sesión','Logout','Fabian','2025-05-04 14:43:52'),
(129,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-04 14:43:56'),
(130,'Cierre de sesión','Logout','Maria Jose ','2025-05-04 14:44:57'),
(131,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-04 14:45:12'),
(132,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-04 14:58:41'),
(133,'Se creó el perfil: pruebas','Creación de perfil','Gloria ','2025-05-04 15:00:23'),
(134,'Actualización de perfil','Se actualizó el perfil con ID 9 (Nombre: pruebas, Estado: inactivo)','Gloria ','2025-05-04 15:27:17'),
(135,'Se creó el perfil: Fabian','Creación de perfil','Gloria ','2025-05-04 15:37:21'),
(136,'Se inhabilitó el perfil con ID 10','Inhabilitación de perfil','Gloria ','2025-05-04 15:44:18'),
(137,'Perfil ID 10 actualizado','Actualización de perfil','Gloria ','2025-05-04 15:44:32'),
(138,'Perfil ID 1 actualizado','Actualización de perfil','Gloria ','2025-05-04 15:44:59'),
(139,'Cierre de sesión','Logout','Gloria ','2025-05-04 15:45:51'),
(140,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-04 15:45:54'),
(141,'Cierre de sesión','Logout','Maria Jose ','2025-05-04 15:47:28'),
(142,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-04 15:47:33'),
(143,'Cierre de sesión','Logout','Gloria ','2025-05-04 15:52:22'),
(144,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-04 15:52:26'),
(145,'Acción del sistema','Inicio de sesión','Maria Jose ','2025-05-04 16:14:46'),
(146,'Cierre de sesión','Logout','Maria Jose ','2025-05-04 16:14:50'),
(147,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-04 16:14:57'),
(148,'Perfil ID 9 actualizado','Actualización de perfil','Gloria ','2025-05-04 16:24:23'),
(149,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-07 16:41:12'),
(150,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-22 21:41:36'),
(151,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 00:39:14'),
(152,'Cierre de sesión','Logout','Gloria ','2025-05-23 00:49:52'),
(153,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 00:49:54'),
(154,'Cierre de sesión','Logout','Gloria ','2025-05-23 00:53:00'),
(155,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 00:53:02'),
(156,'Cierre de sesión','Logout','Gloria ','2025-05-23 00:53:16'),
(157,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 00:54:05'),
(158,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:02:24'),
(159,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:02:26'),
(160,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:02:35'),
(161,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:02:39'),
(162,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:02:48'),
(163,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:02:50'),
(164,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:06:27'),
(165,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:06:29'),
(166,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:06:38'),
(167,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:06:47'),
(168,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:06:59'),
(169,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:07:01'),
(170,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:07:42'),
(171,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:07:45'),
(172,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:07:51'),
(173,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:07:53'),
(174,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:07:57'),
(175,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:08:03'),
(176,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:08:08'),
(177,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:08:10'),
(178,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:11:14'),
(179,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:11:26'),
(180,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:18:04'),
(181,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:18:12'),
(182,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:20:24'),
(183,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:20:47'),
(184,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:33:42'),
(185,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:33:50'),
(186,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:34:36'),
(187,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:34:40'),
(188,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:36:37'),
(189,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:36:41'),
(190,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:36:48'),
(191,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:36:55'),
(192,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:37:06'),
(193,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:37:14'),
(194,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:37:22'),
(195,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:37:23'),
(196,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:38:31'),
(197,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:39:03'),
(198,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:45:37'),
(199,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:45:43'),
(200,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:45:55'),
(201,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:46:02'),
(202,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:46:07'),
(203,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:46:11'),
(204,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:46:27'),
(205,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:46:29'),
(206,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:46:41'),
(207,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 01:46:48'),
(208,'Cierre de sesión','Logout','Gloria ','2025-05-23 01:48:35'),
(209,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 02:19:00'),
(210,'Cierre de sesión','Logout','Gloria ','2025-05-23 02:19:10'),
(211,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 02:19:25'),
(212,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 02:36:47'),
(213,'Cierre de sesión','Logout','Gloria ','2025-05-23 02:37:15'),
(214,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 02:37:17'),
(215,'Cierre de sesión','Logout','Gloria ','2025-05-23 02:37:38'),
(216,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 02:38:09'),
(217,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 02:39:28'),
(218,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 13:15:19'),
(219,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 14:32:00'),
(220,'Cierre de sesión','Logout','Gloria ','2025-05-23 14:50:17'),
(221,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 14:50:19'),
(222,'Cierre de sesión','Logout','Gloria ','2025-05-23 14:59:58'),
(223,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 14:59:59'),
(224,'Cierre de sesión','Logout','Gloria ','2025-05-23 15:10:13'),
(225,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 15:10:15'),
(226,'Se creó el perfil: pruebasÑÑ','Creación de perfil','Gloria ','2025-05-23 15:10:47'),
(227,'Cierre de sesión','Logout','Gloria ','2025-05-23 15:21:50'),
(228,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 15:21:54'),
(229,'Cierre de sesión','Logout','Gloria ','2025-05-23 15:23:18'),
(230,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 15:23:21'),
(231,'Cierre de sesión','Logout','Gloria ','2025-05-23 15:24:46'),
(232,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 15:24:51'),
(233,'Cierre de sesión','Logout','Gloria ','2025-05-23 15:28:13'),
(234,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 15:30:00'),
(235,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 18:18:03'),
(236,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 18:50:24'),
(237,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 18:51:02'),
(238,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:12:22'),
(239,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:15:30'),
(240,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:18:50'),
(241,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:20:27'),
(242,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:25:37'),
(243,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:30:05'),
(244,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:35:41'),
(245,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:40:23'),
(246,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:46:10'),
(247,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:47:47'),
(248,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 19:49:24'),
(249,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 21:23:14'),
(250,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 21:39:23'),
(251,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 21:43:14'),
(252,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 21:53:18'),
(253,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 22:21:07'),
(254,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-23 22:48:59'),
(255,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-24 15:42:39'),
(256,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-24 15:59:51'),
(257,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-24 18:18:58'),
(258,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 12:48:04'),
(259,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 12:56:18'),
(260,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 13:01:17'),
(261,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 13:02:44'),
(262,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 13:03:23'),
(263,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 13:06:06'),
(264,'Se creó el usuario: 1212121 121212','Creación de usuario','Gloria ','2025-05-25 13:20:08'),
(265,'Se creó el perfil: pruebasÑÑq','Creación de perfil','Gloria ','2025-05-25 13:27:59'),
(266,'Se inhabilitó el perfil con ID 12','Inhabilitación de perfil','Gloria ','2025-05-25 13:28:21'),
(267,'Perfil ID 12 actualizado','Actualización de perfil','Gloria ','2025-05-25 13:28:50'),
(268,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 16:46:25'),
(269,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 21:01:56'),
(270,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 22:01:48'),
(271,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-25 22:04:01'),
(272,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 11:59:39'),
(273,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 17:09:09'),
(274,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 17:40:30'),
(275,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 17:59:35'),
(276,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 18:03:54'),
(277,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 18:08:33'),
(278,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 18:19:29'),
(279,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 19:25:50'),
(280,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 19:57:49'),
(281,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 20:01:05'),
(282,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 20:40:06'),
(283,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-26 21:09:21'),
(284,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 02:28:23'),
(285,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 13:25:32'),
(286,'Cierre de sesión','Logout','Gloria ','2025-05-27 15:06:23'),
(287,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 15:06:53'),
(288,'Cierre de sesión','Logout','Gloria ','2025-05-27 15:10:27'),
(289,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 15:10:58'),
(290,'Cierre de sesión','Logout','Gloria ','2025-05-27 15:26:16'),
(291,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 15:26:20'),
(292,'Cierre de sesión','Logout','Gloria ','2025-05-27 15:26:26'),
(293,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 15:26:27'),
(294,'Cierre de sesión','Logout','Gloria ','2025-05-27 15:29:29'),
(295,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 15:29:31'),
(296,'Cierre de sesión','Logout','Gloria ','2025-05-27 15:31:16'),
(297,'Acción del sistema','Inicio de sesión','Gloria ','2025-05-27 15:31:20');
/*!40000 ALTER TABLE `eventos` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `eventos_seguridad`
--

DROP TABLE IF EXISTS `eventos_seguridad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eventos_seguridad` (
  `id_evento` int(11) NOT NULL AUTO_INCREMENT,
  `descripcion` varchar(255) DEFAULT NULL,
  `ip_origen` varchar(45) DEFAULT NULL,
  `ip_destino` varchar(45) DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `tipo` varchar(50) DEFAULT NULL,
  `nivel` varchar(20) DEFAULT NULL,
  `estado_alerta` varchar(10) DEFAULT 'nueva',
  `detalles` longtext DEFAULT NULL,
  `estado_evento` varchar(20) DEFAULT 'activo',
  `mac_origen` varchar(50) DEFAULT NULL,
  `mac_destino` varchar(50) DEFAULT NULL,
  `so_origen` varchar(100) DEFAULT NULL,
  `puerto_origen` varchar(20) DEFAULT NULL,
  `puerto_destino` varchar(20) DEFAULT NULL,
  `protocolo` varchar(20) DEFAULT NULL,
  `repeticiones` int(11) DEFAULT 1,
  PRIMARY KEY (`id_evento`)
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `eventos_seguridad`
--

LOCK TABLES `eventos_seguridad` WRITE;
/*!40000 ALTER TABLE `eventos_seguridad` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `eventos_seguridad` VALUES
(1,'Intento de conexión SYN al servicio MySQL/MariaDB (puerto 3306).','192.168.0.7','192.168.0.2','2025-05-25 10:44:05','Acceso Servicio - MySQL/MariaDB','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 45574, Port_Dst: 3306, Proto: TCP, TTL: 54, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Desconocido','45574','3306','TCP',1),
(2,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 10:44:05','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 45574, Port_Dst: 80, Proto: TCP, TTL: 42, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Desconocido','45574','80','TCP',1),
(3,'Escaneo de Puertos (SYN): 192.168.0.7 escaneó 10 puertos en 192.168.0.2...','192.168.0.7','192.168.0.2','2025-05-25 10:44:05','Reconocimiento - Escaneo SYN','Medio','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 45574, Port_Dst: 554, Proto: TCP, TTL: 44, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Desconocido',NULL,NULL,'TCP',1),
(4,'Intento de conexión SYN al servicio FTP (puerto 21).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - FTP','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 21, Proto: TCP, TTL: 47, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','21','TCP',1),
(5,'Intento de conexión SYN al servicio Telnet (puerto 23).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - Telnet','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 23, Proto: TCP, TTL: 47, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','23','TCP',1),
(6,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 443, Proto: TCP, TTL: 47, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','443','TCP',1),
(7,'Intento de conexión SYN al servicio SMTP (puerto 25).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - SMTP','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 25, Proto: TCP, TTL: 39, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','25','TCP',1),
(8,'Intento de conexión SYN al servicio NetBIOS-SSN (puerto 139).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - NetBIOS-SSN','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 139, Proto: TCP, TTL: 56, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','139','TCP',1),
(9,'Intento de conexión SYN al servicio SMB/CIFS (puerto 445).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - SMB/CIFS','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 445, Proto: TCP, TTL: 42, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','445','TCP',1),
(10,'Intento de conexión SYN al servicio HTTP-Alt (puerto 8080).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - HTTP-Alt','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 8080, Proto: TCP, TTL: 39, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','8080','TCP',1),
(11,'Intento de conexión SYN al servicio SSH (puerto 22).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - SSH','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 22, Proto: TCP, TTL: 42, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','22','TCP',1),
(12,'Intento de conexión SYN al servicio RDP (puerto 3389).','192.168.0.7','192.168.0.253','2025-05-25 10:44:05','Acceso Servicio - RDP','Bajo','nueva','IP_Dst: 192.168.0.253, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 00:00:ca:01:02:03, Port_Src: 45574, Port_Dst: 3389, Proto: TCP, TTL: 38, Flags: S, Size: 58B, SO_Est: Desconocido, Payload: \'\'','activo','d8:80:83:da:d7:b7','00:00:ca:01:02:03','Desconocido','45574','3389','TCP',1),
(13,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.2','2025-05-25 10:45:32','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 2980, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','2980','80','TCP',1),
(14,'Conexión saliente a puerto 5555 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 10:45:45','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 5555, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','5555','TCP',1),
(15,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 10:46:05','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 4568, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','4568','80','TCP',1),
(16,'Conexión saliente a puerto 1337 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 10:46:18','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 1337, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','1337','TCP',1),
(17,'Conexión saliente a puerto 4444 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 10:46:31','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 4444, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','4444','TCP',1),
(18,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','20.42.73.28','2025-05-25 10:48:00','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 20.42.73.28, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 40404, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','40404','443','TCP',1),
(19,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','142.250.218.98','2025-05-25 10:50:05','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 142.250.218.98, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 33150, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','33150','443','TCP',1),
(20,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 10:52:18','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 1592, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','1592','80','TCP',1),
(21,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.2','2025-05-25 10:52:18','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 1612, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','1612','80','TCP',1),
(22,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','51.11.192.48','2025-05-25 10:54:33','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 51.11.192.48, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 58148, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','58148','443','TCP',1),
(23,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 10:57:55','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 2167, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','2167','80','TCP',1),
(24,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.2','2025-05-25 10:57:55','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 2187, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','2187','80','TCP',1),
(25,'Conexión saliente a puerto 5555 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 10:58:51','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 5555, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','5555','TCP',1),
(26,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 10:59:55','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 46377, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','46377','80','TCP',1),
(27,'Posible SYN Flood: 20 SYNs en 0.02s...','192.168.0.7','192.168.0.2','2025-05-25 10:59:55','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 46561, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','46561','80','TCP',1),
(28,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','52.168.112.67','2025-05-25 11:02:10','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 52.168.112.67, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 55084, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','55084','443','TCP',1),
(29,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 11:02:51','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 3020, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','3020','80','TCP',1),
(30,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.2','2025-05-25 11:02:51','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 3040, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','3040','80','TCP',1),
(31,'Conexión saliente a puerto 6667 (potencial C&C).','192.168.0.1','192.168.0.7','2025-05-25 11:04:43','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: 98:f7:81:a9:d2:5f, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 6667, Proto: TCP, TTL: 64, Flags: RA, Size: 60B, SO_Est: Linux/Unix, Payload: \'\0\0\0\0\0\0\'','activo','98:f7:81:a9:d2:5f','d8:80:83:da:d7:b7','Linux/Unix','80','6667','TCP',1),
(32,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','13.89.178.27','2025-05-25 11:06:47','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 13.89.178.27, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 49130, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','49130','443','TCP',1),
(33,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','20.189.173.4','2025-05-25 11:09:12','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 20.189.173.4, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 57396, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','57396','443','TCP',1),
(34,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.1','2025-05-25 11:10:54','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.1, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 3015, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','3015','80','TCP',1),
(35,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.1','2025-05-25 11:10:54','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.1, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 3034, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','3034','80','TCP',1),
(36,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','172.67.41.16','2025-05-25 11:11:26','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 172.67.41.16, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 39362, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','39362','443','TCP',1),
(37,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','142.251.133.98','2025-05-25 11:18:34','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 142.251.133.98, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 34488, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','34488','443','TCP',1),
(38,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.1','2025-05-25 11:20:31','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.1, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 2455, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','2455','80','TCP',1),
(39,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.1','2025-05-25 11:20:31','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.1, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 2475, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','2475','80','TCP',1),
(40,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','172.67.41.16','2025-05-25 11:20:52','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 172.67.41.16, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 54798, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','54798','443','TCP',1),
(41,'Conexión saliente a puerto 5555 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 11:21:33','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 5555, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','5555','TCP',1),
(42,'Conexión saliente a puerto 1337 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 11:21:51','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 1337, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','1337','TCP',1),
(43,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','13.107.6.163','2025-05-25 11:24:18','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 13.107.6.163, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 60188, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','60188','443','TCP',1),
(44,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','20.42.73.28','2025-05-25 11:28:17','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 20.42.73.28, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 33722, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','33722','443','TCP',1),
(45,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','13.107.5.93','2025-05-25 11:32:36','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 13.107.5.93, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 52722, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','52722','443','TCP',1),
(46,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','20.189.173.4','2025-05-25 11:38:48','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 20.189.173.4, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 45162, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','45162','443','TCP',1),
(47,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','52.108.8.12','2025-05-25 11:56:04','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 52.108.8.12, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 52620, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','52620','443','TCP',1),
(48,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.2','2025-05-25 11:57:26','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 2934, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','2934','80','TCP',1),
(49,'Posible SYN Flood: 20 SYNs en 0.02s...','192.168.0.7','192.168.0.2','2025-05-25 11:57:26','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.2, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: f2:3a:6c:1e:89:42, Port_Src: 2953, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','f2:3a:6c:1e:89:42','Linux/Unix','2953','80','TCP',1),
(50,'Conexión saliente a puerto 5555 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 11:57:42','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 5555, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','5555','TCP',1),
(51,'Conexión saliente a puerto 4444 (potencial C&C).','192.168.0.2','192.168.0.7','2025-05-25 11:58:35','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: f2:3a:6c:1e:89:42, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 4444, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','f2:3a:6c:1e:89:42','d8:80:83:da:d7:b7','Linux/Unix','80','4444','TCP',1),
(52,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','140.82.114.25','2025-05-25 12:01:52','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 140.82.114.25, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 57644, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','57644','443','TCP',1),
(53,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','104.208.16.90','2025-05-25 12:05:57','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 104.208.16.90, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 59964, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','59964','443','TCP',1),
(54,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:30:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 2083, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','2083','80','TCP',1),
(55,'Posible SYN Flood: 20 SYNs en 0.02s...','192.168.0.7','192.168.0.9','2025-05-25 16:30:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 2102, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','2102','80','TCP',1),
(56,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','34.89.0.178','2025-05-25 16:30:54','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 34.89.0.178, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 43590, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','43590','443','TCP',1),
(57,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:32:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 27237, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','27237','80','TCP',1),
(58,'Posible SYN Flood: 20 SYNs en 0.02s...','192.168.0.7','192.168.0.9','2025-05-25 16:32:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 28558, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','28558','80','TCP',1),
(59,'Conexión saliente a puerto 6667 (potencial C&C).','192.168.0.9','192.168.0.7','2025-05-25 16:33:57','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: d6:39:36:a7:15:35, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 6667, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','d6:39:36:a7:15:35','d8:80:83:da:d7:b7','Linux/Unix','80','6667','TCP',1),
(60,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:34:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 1141, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','1141','80','TCP',1),
(61,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.9','2025-05-25 16:34:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 4064, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','4064','80','TCP',1),
(62,'Conexión saliente a puerto 4444 (potencial C&C).','192.168.0.9','192.168.0.7','2025-05-25 16:35:13','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: d6:39:36:a7:15:35, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 4444, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','d6:39:36:a7:15:35','d8:80:83:da:d7:b7','Linux/Unix','80','4444','TCP',1),
(63,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:36:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 13316, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','13316','80','TCP',1),
(64,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.9','2025-05-25 16:36:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 16250, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','16250','80','TCP',1),
(65,'Conexión saliente a puerto 5555 (potencial C&C).','192.168.0.9','192.168.0.7','2025-05-25 16:38:02','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: d6:39:36:a7:15:35, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 5555, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','d6:39:36:a7:15:35','d8:80:83:da:d7:b7','Linux/Unix','80','5555','TCP',1),
(66,'Conexión saliente a puerto 6667 (potencial C&C).','192.168.0.9','192.168.0.7','2025-05-25 16:38:13','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: d6:39:36:a7:15:35, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 6667, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','d6:39:36:a7:15:35','d8:80:83:da:d7:b7','Linux/Unix','80','6667','TCP',1),
(67,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:38:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 7988, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','7988','80','TCP',1),
(68,'Posible SYN Flood: 20 SYNs en 0.00s...','192.168.0.7','192.168.0.9','2025-05-25 16:38:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 11378, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','11378','80','TCP',1),
(69,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','52.168.117.169','2025-05-25 16:39:29','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 52.168.117.169, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 50480, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','50480','443','TCP',1),
(70,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:40:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 29622, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','29622','80','TCP',1),
(71,'Posible SYN Flood: 20 SYNs en 0.01s...','192.168.0.7','192.168.0.9','2025-05-25 16:40:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 29420, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','29420','80','TCP',1),
(72,'Intento de conexión SYN al servicio HTTPS (puerto 443).','192.168.0.7','34.87.124.238','2025-05-25 16:41:30','Acceso Servicio - HTTPS','Bajo','nueva','IP_Dst: 34.87.124.238, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: 98:f7:81:a9:d2:5f, Port_Src: 52910, Port_Dst: 443, Proto: TCP, TTL: 64, Flags: S, Size: 74B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','98:f7:81:a9:d2:5f','Linux/Unix','52910','443','TCP',1),
(73,'Conexión saliente a puerto 5555 (potencial C&C).','192.168.0.9','192.168.0.7','2025-05-25 16:42:44','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: d6:39:36:a7:15:35, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 5555, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','d6:39:36:a7:15:35','d8:80:83:da:d7:b7','Linux/Unix','80','5555','TCP',1),
(74,'Intento de conexión SYN al servicio HTTP (puerto 80).','192.168.0.7','192.168.0.9','2025-05-25 16:42:48','Acceso Servicio - HTTP','Bajo','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 60673, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','60673','80','TCP',1),
(75,'Posible SYN Flood: 20 SYNs en 0.00s...','192.168.0.7','192.168.0.9','2025-05-25 16:42:48','DoS - SYN Flood','Alto','nueva','IP_Dst: 192.168.0.9, MAC_Src: d8:80:83:da:d7:b7, MAC_Dst: d6:39:36:a7:15:35, Port_Src: 61585, Port_Dst: 80, Proto: TCP, TTL: 64, Flags: S, Size: 54B, SO_Est: Linux/Unix, Payload: \'\'','activo','d8:80:83:da:d7:b7','d6:39:36:a7:15:35','Linux/Unix','61585','80','TCP',1),
(76,'Conexión saliente a puerto 6667 (potencial C&C).','192.168.0.9','192.168.0.7','2025-05-25 16:43:03','Amenaza - Posible C&C','Alto','nueva','IP_Dst: 192.168.0.7, MAC_Src: d6:39:36:a7:15:35, MAC_Dst: d8:80:83:da:d7:b7, Port_Src: 80, Port_Dst: 6667, Proto: TCP, TTL: 64, Flags: RA, Size: 56B, SO_Est: Linux/Unix, Payload: \'\0\0\'','activo','d6:39:36:a7:15:35','d8:80:83:da:d7:b7','Linux/Unix','80','6667','TCP',1);
/*!40000 ALTER TABLE `eventos_seguridad` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `perfil`
--

DROP TABLE IF EXISTS `perfil`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `perfil` (
  `id_perfil` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `estado` varchar(45) NOT NULL DEFAULT 'activo',
  `descripcion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id_perfil`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `perfil`
--

LOCK TABLES `perfil` WRITE;
/*!40000 ALTER TABLE `perfil` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `perfil` VALUES
(1,'Administrador','activo','Sera el admin con todos los permisos'),
(8,'Cliente','activo',NULL),
(9,'pruebas','activo','null'),
(10,'Fabian','activo','Esto es solo una prueba'),
(11,'pruebasÑÑ','activo','pasta'),
(12,'pruebasÑÑq','activo','qqqqq');
/*!40000 ALTER TABLE `perfil` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `reglas_seguridad`
--

DROP TABLE IF EXISTS `reglas_seguridad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `reglas_seguridad` (
  `id_regla` int(11) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(50) DEFAULT NULL,
  `valor` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_regla`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reglas_seguridad`
--

LOCK TABLES `reglas_seguridad` WRITE;
/*!40000 ALTER TABLE `reglas_seguridad` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `reglas_seguridad` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `apellido` varchar(100) NOT NULL,
  `telefono` varchar(15) NOT NULL,
  `email` varchar(100) NOT NULL,
  `contrasena` varchar(255) NOT NULL,
  `ultimo_acceso` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `id_perfil` int(11) NOT NULL,
  `estado` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `email` (`email`),
  KEY `id_perfil` (`id_perfil`),
  CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`id_perfil`) REFERENCES `perfil` (`id_perfil`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `usuario` VALUES
(10,'Gloria ','Paterina','3134540533','fpaternina12@gmail.comeee','1234','2025-05-04 14:42:37',1,'inactivo'),
(11,'Maria Jose ','Gonzalez','3134540533','mariaberriogonzalez09@gmail.com','1234','2025-05-04 14:43:37',8,'activo'),
(16,'Gloria','Lora','a','d@gmail.com','1','2025-05-03 21:37:51',1,'activo'),
(20,'Fabian','PATERNINA','3134540533','nuevoadmin@ejemplo.com','admin123','2025-05-04 14:43:12',1,'activo'),
(22,'1212121','121212','12121212','fpaternina12@gmail.comeee11','12341212','2025-05-25 13:20:08',10,'activo');
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;
commit;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-05-27 10:50:23
