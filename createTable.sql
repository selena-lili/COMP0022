CREATE DATABASE IF NOT EXISTS `COMP0022` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `COMP0022`;

CREATE TABLE IF NOT EXISTS `accounts` (
	`id` int(11) NOT NULL AUTO_INCREMENT,
  	`username` varchar(50) NOT NULL,
  	`password` varchar(255) NOT NULL,
  	`email` varchar(100) NOT NULL,
  	`phone` varchar(15) NOT NULL,
  	`address` varchar(100) NOT NULL,
  	`postcode` varchar(10) NOT NULL,
  	`country` varchar(50) NOT NULL DEFAULT 'United Kingdom',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;