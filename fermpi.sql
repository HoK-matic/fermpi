-- phpMyAdmin SQL Dump
-- version 4.6.6deb4
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Erstellungszeit: 10. Jan 2018 um 10:32
-- Server-Version: 10.1.23-MariaDB-9+deb9u1
-- PHP-Version: 7.0.19-1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `fermpi`
--
-- DROP DATABASE IF EXISTS `fermpi`;
CREATE DATABASE IF NOT EXISTS `fermpi` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `fermpi`;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `config`
--

-- DROP TABLE IF EXISTS `config`;
CREATE TABLE `config` (
  `id` int(10) UNSIGNED NOT NULL,
  `item` varchar(16) NOT NULL,
  `value` varchar(24) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `fermentations`
--

-- DROP TABLE IF EXISTS `fermentations`;
CREATE TABLE `fermentations` (
  `id` int(10) UNSIGNED NOT NULL,
  `name` varchar(32) NOT NULL,
  `t1` varchar(7) DEFAULT NULL,
  `d1` int(11) DEFAULT NULL,
  `t2` varchar(7) DEFAULT NULL,
  `d2` int(11) DEFAULT NULL,
  `t3` varchar(7) DEFAULT NULL,
  `d3` int(11) DEFAULT NULL,
  `t4` varchar(7) DEFAULT NULL,
  `d4` int(11) DEFAULT NULL,
  `t5` varchar(7) DEFAULT NULL,
  `d5` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `logs`
--

-- DROP TABLE IF EXISTS `logs`;
CREATE TABLE `logs` (
  `id` bigint(10) UNSIGNED NOT NULL,
  `fermentation` int(10) UNSIGNED NOT NULL,
  `sensor` tinyint(3) UNSIGNED NOT NULL,
  `temperature` varchar(7) NOT NULL,
  `timestamp` varchar(24) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `profiles`
--

-- DROP TABLE IF EXISTS `profiles`;
CREATE TABLE `profiles` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `mode` tinyint(3) UNSIGNED NOT NULL,
  `name` varchar(32) NOT NULL,
  `t1` varchar(7) NOT NULL,
  `d1` int(11) DEFAULT NULL,
  `t2` varchar(7) DEFAULT NULL,
  `d2` int(11) DEFAULT NULL,
  `t3` varchar(7) DEFAULT NULL,
  `d3` int(11) DEFAULT NULL,
  `t4` varchar(7) DEFAULT NULL,
  `d4` int(11) DEFAULT NULL,
  `t5` varchar(7) DEFAULT NULL,
  `d5` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `sensors`
--

-- DROP TABLE IF EXISTS `sensors`;
CREATE TABLE `sensors` (
  `id` tinyint(1) UNSIGNED NOT NULL,
  `sensor` varchar(13) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `config`
--
ALTER TABLE `config`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `item` (`item`);

--
-- Indizes für die Tabelle `fermentations`
--
ALTER TABLE `fermentations`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `FIDX` (`name`);

--
-- Indizes für die Tabelle `logs`
--
ALTER TABLE `logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `LOG` (`fermentation`,`sensor`,`timestamp`);

--
-- Indizes für die Tabelle `profiles`
--
ALTER TABLE `profiles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indizes für die Tabelle `sensors`
--
ALTER TABLE `sensors`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `sensor` (`sensor`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `config`
--
ALTER TABLE `config`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT für Tabelle `fermentations`
--
ALTER TABLE `fermentations`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT für Tabelle `logs`
--
ALTER TABLE `logs`
  MODIFY `id` bigint(10) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT für Tabelle `profiles`
--
ALTER TABLE `profiles`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT für Tabelle `sensors`
--
ALTER TABLE `sensors`
  MODIFY `id` tinyint(1) UNSIGNED NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
