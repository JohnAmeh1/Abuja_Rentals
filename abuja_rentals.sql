-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 12, 2026 at 01:07 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `abuja_rentals`
--

-- --------------------------------------------------------

--
-- Table structure for table `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 2, 'add_permission'),
(6, 'Can change permission', 2, 'change_permission'),
(7, 'Can delete permission', 2, 'delete_permission'),
(8, 'Can view permission', 2, 'view_permission'),
(9, 'Can add group', 3, 'add_group'),
(10, 'Can change group', 3, 'change_group'),
(11, 'Can delete group', 3, 'delete_group'),
(12, 'Can view group', 3, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add property', 7, 'add_property'),
(26, 'Can change property', 7, 'change_property'),
(27, 'Can delete property', 7, 'delete_property'),
(28, 'Can view property', 7, 'view_property'),
(29, 'Can add wallet', 8, 'add_wallet'),
(30, 'Can change wallet', 8, 'change_wallet'),
(31, 'Can delete wallet', 8, 'delete_wallet'),
(32, 'Can view wallet', 8, 'view_wallet'),
(33, 'Can add user profile', 9, 'add_userprofile'),
(34, 'Can change user profile', 9, 'change_userprofile'),
(35, 'Can delete user profile', 9, 'delete_userprofile'),
(36, 'Can view user profile', 9, 'view_userprofile'),
(37, 'Can add transaction', 10, 'add_transaction'),
(38, 'Can change transaction', 10, 'change_transaction'),
(39, 'Can delete transaction', 10, 'delete_transaction'),
(40, 'Can view transaction', 10, 'view_transaction'),
(41, 'Can add property visit', 11, 'add_propertyvisit'),
(42, 'Can change property visit', 11, 'change_propertyvisit'),
(43, 'Can delete property visit', 11, 'delete_propertyvisit'),
(44, 'Can view property visit', 11, 'view_propertyvisit'),
(45, 'Can add property rental', 12, 'add_propertyrental'),
(46, 'Can change property rental', 12, 'change_propertyrental'),
(47, 'Can delete property rental', 12, 'delete_propertyrental'),
(48, 'Can view property rental', 12, 'view_propertyrental'),
(49, 'Can add property ownership', 13, 'add_propertyownership'),
(50, 'Can change property ownership', 13, 'change_propertyownership'),
(51, 'Can delete property ownership', 13, 'delete_propertyownership'),
(52, 'Can view property ownership', 13, 'view_propertyownership'),
(53, 'Can add property inquiry', 14, 'add_propertyinquiry'),
(54, 'Can change property inquiry', 14, 'change_propertyinquiry'),
(55, 'Can delete property inquiry', 14, 'delete_propertyinquiry'),
(56, 'Can view property inquiry', 14, 'view_propertyinquiry'),
(57, 'Can add admin message', 15, 'add_adminmessage'),
(58, 'Can change admin message', 15, 'change_adminmessage'),
(59, 'Can delete admin message', 15, 'delete_adminmessage'),
(60, 'Can view admin message', 15, 'view_adminmessage'),
(61, 'Can add saved property', 16, 'add_savedproperty'),
(62, 'Can change saved property', 16, 'change_savedproperty'),
(63, 'Can delete saved property', 16, 'delete_savedproperty'),
(64, 'Can view saved property', 16, 'view_savedproperty'),
(65, 'Can add report', 17, 'add_report'),
(66, 'Can change report', 17, 'change_report'),
(67, 'Can delete report', 17, 'delete_report'),
(68, 'Can view report', 17, 'view_report'),
(69, 'Can add Student Property', 18, 'add_studentproperty'),
(70, 'Can change Student Property', 18, 'change_studentproperty'),
(71, 'Can delete Student Property', 18, 'delete_studentproperty'),
(72, 'Can view Student Property', 18, 'view_studentproperty'),
(73, 'Can add Student Property Rental', 19, 'add_studentpropertyrental'),
(74, 'Can change Student Property Rental', 19, 'change_studentpropertyrental'),
(75, 'Can delete Student Property Rental', 19, 'delete_studentpropertyrental'),
(76, 'Can view Student Property Rental', 19, 'view_studentpropertyrental');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user`
--

CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(1, 'pbkdf2_sha256$600000$BwFpU7O1jAlkGCxEMwG4jh$SJWd5SvXgdZnFk5FO4WC2D0bW5fQncFEwnyuArgOelc=', '2026-01-12 12:06:11.365945', 1, 'JohnAmeh', '', '', 'johnameh29@gmail.com', 1, 1, '2026-01-12 12:04:34.979307');

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_groups`
--

CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `auth_user_user_permissions`
--

CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(3, 'auth', 'group'),
(2, 'auth', 'permission'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(15, 'rentals', 'adminmessage'),
(7, 'rentals', 'property'),
(14, 'rentals', 'propertyinquiry'),
(13, 'rentals', 'propertyownership'),
(12, 'rentals', 'propertyrental'),
(11, 'rentals', 'propertyvisit'),
(17, 'rentals', 'report'),
(16, 'rentals', 'savedproperty'),
(18, 'rentals', 'studentproperty'),
(19, 'rentals', 'studentpropertyrental'),
(10, 'rentals', 'transaction'),
(9, 'rentals', 'userprofile'),
(8, 'rentals', 'wallet'),
(6, 'sessions', 'session');

-- --------------------------------------------------------

--
-- Table structure for table `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2026-01-12 12:01:23.491412'),
(2, 'auth', '0001_initial', '2026-01-12 12:01:23.879600'),
(3, 'admin', '0001_initial', '2026-01-12 12:01:24.081698'),
(4, 'admin', '0002_logentry_remove_auto_add', '2026-01-12 12:01:24.090920'),
(5, 'admin', '0003_logentry_add_action_flag_choices', '2026-01-12 12:01:24.101506'),
(6, 'contenttypes', '0002_remove_content_type_name', '2026-01-12 12:01:24.159577'),
(7, 'auth', '0002_alter_permission_name_max_length', '2026-01-12 12:01:24.206240'),
(8, 'auth', '0003_alter_user_email_max_length', '2026-01-12 12:01:24.225993'),
(9, 'auth', '0004_alter_user_username_opts', '2026-01-12 12:01:24.236786'),
(10, 'auth', '0005_alter_user_last_login_null', '2026-01-12 12:01:24.308943'),
(11, 'auth', '0006_require_contenttypes_0002', '2026-01-12 12:01:24.312306'),
(12, 'auth', '0007_alter_validators_add_error_messages', '2026-01-12 12:01:24.322306'),
(13, 'auth', '0008_alter_user_username_max_length', '2026-01-12 12:01:24.344222'),
(14, 'auth', '0009_alter_user_last_name_max_length', '2026-01-12 12:01:24.410466'),
(15, 'auth', '0010_alter_group_name_max_length', '2026-01-12 12:01:24.456757'),
(16, 'auth', '0011_update_proxy_permissions', '2026-01-12 12:01:24.466180'),
(17, 'auth', '0012_alter_user_first_name_max_length', '2026-01-12 12:01:24.489676'),
(18, 'rentals', '0001_initial', '2026-01-12 12:01:25.307973'),
(19, 'rentals', '0002_alter_property_address', '2026-01-12 12:01:25.325999'),
(20, 'rentals', '0003_userprofile_whatsapp_link', '2026-01-12 12:01:25.363608'),
(21, 'rentals', '0004_alter_userprofile_user_type', '2026-01-12 12:01:25.381627'),
(22, 'rentals', '0005_report', '2026-01-12 12:01:25.557823'),
(23, 'rentals', '0006_alter_userprofile_user_type_studentproperty', '2026-01-12 12:01:25.714281'),
(24, 'rentals', '0007_studentproperty_university', '2026-01-12 12:01:25.745679'),
(25, 'rentals', '0008_alter_studentproperty_status', '2026-01-12 12:01:25.774411'),
(26, 'rentals', '0009_studentpropertyrental', '2026-01-12 12:01:25.894855'),
(27, 'sessions', '0001_initial', '2026-01-12 12:01:25.920576');

-- --------------------------------------------------------

--
-- Table structure for table `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('s3ak23b0s491b0ak6t7k9hqwzcqz4oyq', '.eJxVjMsKwjAQAP9lzxKax6a1R-9-Q9hmtzYqiTQtKOK_S6EHvc4M84ZA6zKFtcocEkMPGg6_bKB4k7wJvlK-FBVLXuY0qC1Ru63qXFjup739G0xUJ-gBR3QiXrwwaTaGXCsuku3ENt5Y3fqxbQQ5On9E6ZCQB9GRDGN3tDhu0yq1ppKDPB9pfkHffL6j3D95:1vfGgV:ng0zIkujVuz3BgpxtA0LCLngqiFYyRMRNRv2A8sU6P4', '2026-01-26 12:06:11.376618');

-- --------------------------------------------------------

--
-- Table structure for table `rentals_adminmessage`
--

CREATE TABLE `rentals_adminmessage` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` longtext NOT NULL,
  `message_type` varchar(20) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `show_to_all` tinyint(1) NOT NULL,
  `show_to_owners` tinyint(1) NOT NULL,
  `show_to_tenants` tinyint(1) NOT NULL,
  `start_date` datetime(6) NOT NULL,
  `end_date` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_property`
--

CREATE TABLE `rentals_property` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `property_type` varchar(20) NOT NULL,
  `purpose` varchar(10) NOT NULL,
  `status` varchar(10) NOT NULL,
  `address` varchar(255) NOT NULL,
  `city` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `zip_code` varchar(20) NOT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `bedrooms` int(10) UNSIGNED DEFAULT NULL CHECK (`bedrooms` >= 0),
  `bathrooms` int(10) UNSIGNED DEFAULT NULL CHECK (`bathrooms` >= 0),
  `area_sqft` decimal(10,2) DEFAULT NULL,
  `price` decimal(12,2) NOT NULL,
  `platform_fee` decimal(12,2) NOT NULL,
  `net_amount` decimal(12,2) NOT NULL,
  `rent_duration_months` int(10) UNSIGNED DEFAULT NULL CHECK (`rent_duration_months` >= 0),
  `amenities` longtext NOT NULL,
  `main_image` varchar(100) NOT NULL,
  `image_1` varchar(100) DEFAULT NULL,
  `image_2` varchar(100) DEFAULT NULL,
  `image_3` varchar(100) DEFAULT NULL,
  `image_4` varchar(100) DEFAULT NULL,
  `image_5` varchar(100) DEFAULT NULL,
  `is_featured` tinyint(1) NOT NULL,
  `views` int(10) UNSIGNED NOT NULL CHECK (`views` >= 0),
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `published_at` datetime(6) DEFAULT NULL,
  `sale_price` decimal(12,2) DEFAULT NULL,
  `sold_at` datetime(6) DEFAULT NULL,
  `owner_id` int(11) NOT NULL,
  `rented_to_id` int(11) DEFAULT NULL,
  `sold_to_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_propertyinquiry`
--

CREATE TABLE `rentals_propertyinquiry` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(254) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `message` longtext NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_propertyownership`
--

CREATE TABLE `rentals_propertyownership` (
  `id` int(11) NOT NULL,
  `purchase_price` decimal(12,2) NOT NULL,
  `purchased_at` datetime(6) NOT NULL,
  `ownership_document` varchar(100) DEFAULT NULL,
  `owner_id` int(11) NOT NULL,
  `property_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_propertyrental`
--

CREATE TABLE `rentals_propertyrental` (
  `id` int(11) NOT NULL,
  `monthly_rent` decimal(10,2) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `deposit` decimal(10,2) NOT NULL,
  `total_amount` decimal(12,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_propertyvisit`
--

CREATE TABLE `rentals_propertyvisit` (
  `id` int(11) NOT NULL,
  `visit_date` date NOT NULL,
  `visit_time` time(6) NOT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `owner_response` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `visitor_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_report`
--

CREATE TABLE `rentals_report` (
  `id` int(11) NOT NULL,
  `reason` varchar(50) NOT NULL,
  `message` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `admin_action` longtext NOT NULL,
  `property_id` int(11) DEFAULT NULL,
  `reported_user_id` int(11) NOT NULL,
  `reporter_id` int(11) NOT NULL,
  `resolved_by_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_savedproperty`
--

CREATE TABLE `rentals_savedproperty` (
  `id` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_studentpropertyrental`
--

CREATE TABLE `rentals_studentpropertyrental` (
  `id` int(11) NOT NULL,
  `monthly_rent` decimal(10,2) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `deposit` decimal(10,2) NOT NULL,
  `total_amount` decimal(12,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_transaction`
--

CREATE TABLE `rentals_transaction` (
  `id` int(11) NOT NULL,
  `transaction_type` varchar(20) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `reference` varchar(50) DEFAULT NULL,
  `related_property_id` int(11) DEFAULT NULL,
  `related_property_title` varchar(200) NOT NULL,
  `wallet_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `rentals_userprofile`
--

CREATE TABLE `rentals_userprofile` (
  `id` int(11) NOT NULL,
  `user_type` varchar(10) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `profile_picture` varchar(100) DEFAULT NULL,
  `bio` longtext NOT NULL,
  `address` varchar(255) NOT NULL,
  `email_verified` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL,
  `whatsapp_link` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `rentals_userprofile`
--

INSERT INTO `rentals_userprofile` (`id`, `user_type`, `phone_number`, `profile_picture`, `bio`, `address`, `email_verified`, `created_at`, `updated_at`, `user_id`, `whatsapp_link`) VALUES
(1, 'admin', '', '', '', '', 0, '2026-01-12 12:04:35.535858', '2026-01-12 12:06:11.370788', 1, '');

-- --------------------------------------------------------

--
-- Table structure for table `rentals_wallet`
--

CREATE TABLE `rentals_wallet` (
  `id` int(11) NOT NULL,
  `balance` decimal(12,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `rentals_wallet`
--

INSERT INTO `rentals_wallet` (`id`, `balance`, `created_at`, `updated_at`, `user_id`) VALUES
(1, 0.00, '2026-01-12 12:04:35.540357', '2026-01-12 12:06:11.374026', 1);

-- --------------------------------------------------------

--
-- Table structure for table `student_property`
--

CREATE TABLE `student_property` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `property_type` varchar(20) NOT NULL,
  `purpose` varchar(10) NOT NULL,
  `status` varchar(20) NOT NULL,
  `city` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `zip_code` varchar(10) DEFAULT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `bedrooms` int(11) DEFAULT NULL,
  `bathrooms` int(11) DEFAULT NULL,
  `area_sqft` decimal(10,2) DEFAULT NULL,
  `price` decimal(12,2) NOT NULL,
  `platform_fee` decimal(12,2) NOT NULL,
  `net_amount` decimal(12,2) NOT NULL,
  `sale_price` decimal(12,2) DEFAULT NULL,
  `rent_duration_months` int(11) DEFAULT NULL,
  `amenities` longtext DEFAULT NULL,
  `main_image` varchar(100) NOT NULL,
  `image_1` varchar(100) DEFAULT NULL,
  `image_2` varchar(100) DEFAULT NULL,
  `image_3` varchar(100) DEFAULT NULL,
  `image_4` varchar(100) DEFAULT NULL,
  `image_5` varchar(100) DEFAULT NULL,
  `is_featured` tinyint(1) NOT NULL,
  `views` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `published_at` datetime(6) DEFAULT NULL,
  `sold_at` datetime(6) DEFAULT NULL,
  `created_by_id` int(11) NOT NULL,
  `rented_to_id` int(11) DEFAULT NULL,
  `university` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Indexes for table `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

--
-- Indexes for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

--
-- Indexes for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`);

--
-- Indexes for table `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Indexes for table `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- Indexes for table `rentals_adminmessage`
--
ALTER TABLE `rentals_adminmessage`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_adminmessage_created_by_id_bd574e7d_fk_auth_user_id` (`created_by_id`);

--
-- Indexes for table `rentals_property`
--
ALTER TABLE `rentals_property`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_property_owner_id_7b5127d2_fk_auth_user_id` (`owner_id`),
  ADD KEY `rentals_property_rented_to_id_c91274cc_fk_auth_user_id` (`rented_to_id`),
  ADD KEY `rentals_property_sold_to_id_25388af4_fk_auth_user_id` (`sold_to_id`);

--
-- Indexes for table `rentals_propertyinquiry`
--
ALTER TABLE `rentals_propertyinquiry`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_propertyinqu_property_id_d44719a1_fk_rentals_p` (`property_id`),
  ADD KEY `rentals_propertyinquiry_sender_id_db10aed2_fk_auth_user_id` (`sender_id`);

--
-- Indexes for table `rentals_propertyownership`
--
ALTER TABLE `rentals_propertyownership`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `property_id` (`property_id`),
  ADD KEY `rentals_propertyownership_owner_id_cd21b134_fk_auth_user_id` (`owner_id`);

--
-- Indexes for table `rentals_propertyrental`
--
ALTER TABLE `rentals_propertyrental`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_propertyrent_property_id_a635dc88_fk_rentals_p` (`property_id`),
  ADD KEY `rentals_propertyrental_tenant_id_ad52e5a5_fk_auth_user_id` (`tenant_id`);

--
-- Indexes for table `rentals_propertyvisit`
--
ALTER TABLE `rentals_propertyvisit`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_propertyvisi_property_id_19a5b609_fk_rentals_p` (`property_id`),
  ADD KEY `rentals_propertyvisit_visitor_id_f35cecfe_fk_auth_user_id` (`visitor_id`);

--
-- Indexes for table `rentals_report`
--
ALTER TABLE `rentals_report`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_report_property_id_38feaf5b_fk_rentals_property_id` (`property_id`),
  ADD KEY `rentals_report_reported_user_id_170da1d8_fk_auth_user_id` (`reported_user_id`),
  ADD KEY `rentals_report_reporter_id_3d7724ec_fk_auth_user_id` (`reporter_id`),
  ADD KEY `rentals_report_resolved_by_id_b328345f_fk_auth_user_id` (`resolved_by_id`);

--
-- Indexes for table `rentals_savedproperty`
--
ALTER TABLE `rentals_savedproperty`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `rentals_savedproperty_user_id_property_id_3fd6b2b4_uniq` (`user_id`,`property_id`),
  ADD KEY `rentals_savedpropert_property_id_f84feb9d_fk_rentals_p` (`property_id`);

--
-- Indexes for table `rentals_studentpropertyrental`
--
ALTER TABLE `rentals_studentpropertyrental`
  ADD PRIMARY KEY (`id`),
  ADD KEY `rentals_studentprope_property_id_91554aea_fk_student_p` (`property_id`),
  ADD KEY `rentals_studentpropertyrental_tenant_id_d053a6af_fk_auth_user_id` (`tenant_id`);

--
-- Indexes for table `rentals_transaction`
--
ALTER TABLE `rentals_transaction`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `reference` (`reference`),
  ADD KEY `rentals_transaction_wallet_id_1b870fc1_fk_rentals_wallet_id` (`wallet_id`);

--
-- Indexes for table `rentals_userprofile`
--
ALTER TABLE `rentals_userprofile`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Indexes for table `rentals_wallet`
--
ALTER TABLE `rentals_wallet`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Indexes for table `student_property`
--
ALTER TABLE `student_property`
  ADD PRIMARY KEY (`id`),
  ADD KEY `student_property_created_by_id_b37a898d_fk_auth_user_id` (`created_by_id`),
  ADD KEY `student_property_rented_to_id_f67d4a73_fk_auth_user_id` (`rented_to_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=77;

--
-- AUTO_INCREMENT for table `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=20;

--
-- AUTO_INCREMENT for table `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT for table `rentals_adminmessage`
--
ALTER TABLE `rentals_adminmessage`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_property`
--
ALTER TABLE `rentals_property`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_propertyinquiry`
--
ALTER TABLE `rentals_propertyinquiry`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_propertyownership`
--
ALTER TABLE `rentals_propertyownership`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_propertyrental`
--
ALTER TABLE `rentals_propertyrental`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_propertyvisit`
--
ALTER TABLE `rentals_propertyvisit`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_report`
--
ALTER TABLE `rentals_report`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_savedproperty`
--
ALTER TABLE `rentals_savedproperty`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_studentpropertyrental`
--
ALTER TABLE `rentals_studentpropertyrental`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_transaction`
--
ALTER TABLE `rentals_transaction`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `rentals_userprofile`
--
ALTER TABLE `rentals_userprofile`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `rentals_wallet`
--
ALTER TABLE `rentals_wallet`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `student_property`
--
ALTER TABLE `student_property`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Constraints for table `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Constraints for table `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_adminmessage`
--
ALTER TABLE `rentals_adminmessage`
  ADD CONSTRAINT `rentals_adminmessage_created_by_id_bd574e7d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_property`
--
ALTER TABLE `rentals_property`
  ADD CONSTRAINT `rentals_property_owner_id_7b5127d2_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `rentals_property_rented_to_id_c91274cc_fk_auth_user_id` FOREIGN KEY (`rented_to_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `rentals_property_sold_to_id_25388af4_fk_auth_user_id` FOREIGN KEY (`sold_to_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_propertyinquiry`
--
ALTER TABLE `rentals_propertyinquiry`
  ADD CONSTRAINT `rentals_propertyinqu_property_id_d44719a1_fk_rentals_p` FOREIGN KEY (`property_id`) REFERENCES `rentals_property` (`id`),
  ADD CONSTRAINT `rentals_propertyinquiry_sender_id_db10aed2_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_propertyownership`
--
ALTER TABLE `rentals_propertyownership`
  ADD CONSTRAINT `rentals_propertyowne_property_id_fc548443_fk_rentals_p` FOREIGN KEY (`property_id`) REFERENCES `rentals_property` (`id`),
  ADD CONSTRAINT `rentals_propertyownership_owner_id_cd21b134_fk_auth_user_id` FOREIGN KEY (`owner_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_propertyrental`
--
ALTER TABLE `rentals_propertyrental`
  ADD CONSTRAINT `rentals_propertyrent_property_id_a635dc88_fk_rentals_p` FOREIGN KEY (`property_id`) REFERENCES `rentals_property` (`id`),
  ADD CONSTRAINT `rentals_propertyrental_tenant_id_ad52e5a5_fk_auth_user_id` FOREIGN KEY (`tenant_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_propertyvisit`
--
ALTER TABLE `rentals_propertyvisit`
  ADD CONSTRAINT `rentals_propertyvisi_property_id_19a5b609_fk_rentals_p` FOREIGN KEY (`property_id`) REFERENCES `rentals_property` (`id`),
  ADD CONSTRAINT `rentals_propertyvisit_visitor_id_f35cecfe_fk_auth_user_id` FOREIGN KEY (`visitor_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_report`
--
ALTER TABLE `rentals_report`
  ADD CONSTRAINT `rentals_report_property_id_38feaf5b_fk_rentals_property_id` FOREIGN KEY (`property_id`) REFERENCES `rentals_property` (`id`),
  ADD CONSTRAINT `rentals_report_reported_user_id_170da1d8_fk_auth_user_id` FOREIGN KEY (`reported_user_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `rentals_report_reporter_id_3d7724ec_fk_auth_user_id` FOREIGN KEY (`reporter_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `rentals_report_resolved_by_id_b328345f_fk_auth_user_id` FOREIGN KEY (`resolved_by_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_savedproperty`
--
ALTER TABLE `rentals_savedproperty`
  ADD CONSTRAINT `rentals_savedpropert_property_id_f84feb9d_fk_rentals_p` FOREIGN KEY (`property_id`) REFERENCES `rentals_property` (`id`),
  ADD CONSTRAINT `rentals_savedproperty_user_id_32c00772_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_studentpropertyrental`
--
ALTER TABLE `rentals_studentpropertyrental`
  ADD CONSTRAINT `rentals_studentprope_property_id_91554aea_fk_student_p` FOREIGN KEY (`property_id`) REFERENCES `student_property` (`id`),
  ADD CONSTRAINT `rentals_studentpropertyrental_tenant_id_d053a6af_fk_auth_user_id` FOREIGN KEY (`tenant_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_transaction`
--
ALTER TABLE `rentals_transaction`
  ADD CONSTRAINT `rentals_transaction_wallet_id_1b870fc1_fk_rentals_wallet_id` FOREIGN KEY (`wallet_id`) REFERENCES `rentals_wallet` (`id`);

--
-- Constraints for table `rentals_userprofile`
--
ALTER TABLE `rentals_userprofile`
  ADD CONSTRAINT `rentals_userprofile_user_id_748f5bd2_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `rentals_wallet`
--
ALTER TABLE `rentals_wallet`
  ADD CONSTRAINT `rentals_wallet_user_id_05fee7a8_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Constraints for table `student_property`
--
ALTER TABLE `student_property`
  ADD CONSTRAINT `student_property_created_by_id_b37a898d_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  ADD CONSTRAINT `student_property_rented_to_id_f67d4a73_fk_auth_user_id` FOREIGN KEY (`rented_to_id`) REFERENCES `auth_user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
