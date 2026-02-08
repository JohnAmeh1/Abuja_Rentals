-- Abuja Rentals Database Schema (External Payment API Version)
-- Refactored to remove wallet and integrate with external payment providers

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- =====================================================
-- AUTH & PERMISSION TABLES (Django Built-in)
-- =====================================================

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =====================================================
-- CUSTOM APP TABLES (Rentals)
-- =====================================================

-- User Profile
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
  `user_id` int(11) NOT NULL UNIQUE,
  `whatsapp_link` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Property Management
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
  `sold_to_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`),
  KEY `rented_to_id` (`rented_to_id`),
  KEY `sold_to_id` (`sold_to_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Property Ownership
CREATE TABLE `rentals_propertyownership` (
  `id` int(11) NOT NULL,
  `purchase_price` decimal(12,2) NOT NULL,
  `purchased_at` datetime(6) NOT NULL,
  `ownership_document` varchar(100) DEFAULT NULL,
  `owner_id` int(11) NOT NULL,
  `property_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`),
  KEY `property_id` (`property_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Property Rental Agreement
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
  `tenant_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Student Property Rental (Specialized)
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
  `tenant_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Student Property (Specialized)
CREATE TABLE `rentals_studentproperty` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `property_type` varchar(20) NOT NULL,
  `status` varchar(10) NOT NULL,
  `address` varchar(255) NOT NULL,
  `city` varchar(100) NOT NULL,
  `bedrooms` int(10) UNSIGNED DEFAULT NULL CHECK (`bedrooms` >= 0),
  `bathrooms` int(10) UNSIGNED DEFAULT NULL CHECK (`bathrooms` >= 0),
  `price` decimal(12,2) NOT NULL,
  `platform_fee` decimal(12,2) NOT NULL,
  `net_amount` decimal(12,2) NOT NULL,
  `amenities` longtext NOT NULL,
  `main_image` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `owner_id` int(11) NOT NULL,
  `university` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =====================================================
-- PAYMENT TRACKING (External API Integration)
-- =====================================================

-- Payment Records (for external payment providers like Stripe, PayPal, etc.)
CREATE TABLE `rentals_payment` (
  `id` int(11) NOT NULL,
  `payment_provider` varchar(50) NOT NULL,
  `external_payment_id` varchar(255) NOT NULL UNIQUE,
  `user_id` int(11) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) DEFAULT 'NGN',
  `status` varchar(20) NOT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  `description` longtext NOT NULL,
  `related_property_id` int(11) DEFAULT NULL,
  `related_rental_id` int(11) DEFAULT NULL,
  `metadata` longtext,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `paid_at` datetime(6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `external_payment_id` (`external_payment_id`),
  KEY `status` (`status`),
  KEY `created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Transaction History (for user records and auditing)
CREATE TABLE `rentals_transaction` (
  `id` int(11) NOT NULL,
  `transaction_type` varchar(20) NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(20) DEFAULT 'completed',
  `created_at` datetime(6) NOT NULL,
  `reference` varchar(50) DEFAULT NULL,
  `related_property_id` int(11) DEFAULT NULL,
  `related_property_title` varchar(200) NOT NULL,
  `user_id` int(11) NOT NULL,
  `payment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `payment_id` (`payment_id`),
  KEY `created_at` (`created_at`),
  FOREIGN KEY (`payment_id`) REFERENCES `rentals_payment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =====================================================
-- USER INTERACTIONS
-- =====================================================

-- Property Visits/Tours
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
  `visitor_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `visitor_id` (`visitor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Property Inquiries
CREATE TABLE `rentals_propertyinquiry` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(254) NOT NULL,
  `phone` varchar(15) NOT NULL,
  `message` longtext NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `sender_id` (`sender_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Saved Properties (Wishlist)
CREATE TABLE `rentals_savedproperty` (
  `id` int(11) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `property_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =====================================================
-- MODERATION & REPORTING
-- =====================================================

-- Reports
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
  `resolved_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `property_id` (`property_id`),
  KEY `reported_user_id` (`reported_user_id`),
  KEY `reporter_id` (`reporter_id`),
  KEY `resolved_by_id` (`resolved_by_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Admin Messages
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
  `created_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `created_by_id` (`created_by_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- =====================================================
-- INDEXES FOR PRIMARY KEYS
-- =====================================================

ALTER TABLE `auth_group` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `name` (`name`);
ALTER TABLE `auth_group_permissions` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`), ADD KEY `auth_group_permissions_permission_id_84c5c92e_fk_auth_permission_id` (`permission_id`);
ALTER TABLE `auth_permission` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`), ADD KEY `auth_permission_content_type_id_2f476e4b_fk_django_co` (`content_type_id`);
ALTER TABLE `auth_user` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `username` (`username`), ADD UNIQUE KEY `email` (`email`);
ALTER TABLE `auth_user_groups` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`), ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);
ALTER TABLE `auth_user_user_permissions` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`), ADD KEY `auth_user_user_permissions_permission_id_b5644425_fk_auth_permission_id` (`permission_id`);
ALTER TABLE `django_admin_log` ADD PRIMARY KEY (`id`), ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`), ADD KEY `django_admin_log_user_id_c564ebb4_fk_auth_user_id` (`user_id`);
ALTER TABLE `django_content_type` ADD PRIMARY KEY (`id`), ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);
ALTER TABLE `django_session` ADD PRIMARY KEY (`session_key`), ADD KEY `django_session_expire_date_a5c62663_idx` (`expire_date`);
ALTER TABLE `django_migrations` ADD PRIMARY KEY (`id`);
ALTER TABLE `rentals_userprofile` ADD PRIMARY KEY (`id`), ADD KEY `user_id` (`user_id`);
ALTER TABLE `rentals_property` ADD KEY `owner_id` (`owner_id`);
ALTER TABLE `rentals_propertyownership` ADD KEY `owner_id` (`owner_id`);
ALTER TABLE `rentals_propertyrental` ADD KEY `property_id` (`property_id`);
ALTER TABLE `rentals_studentpropertyrental` ADD KEY `property_id` (`property_id`);
ALTER TABLE `rentals_studentproperty` ADD KEY `owner_id` (`owner_id`);
ALTER TABLE `rentals_payment` ADD KEY `user_id` (`user_id`);
ALTER TABLE `rentals_transaction` ADD KEY `user_id` (`user_id`);
ALTER TABLE `rentals_propertyvisit` ADD KEY `property_id` (`property_id`);
ALTER TABLE `rentals_propertyinquiry` ADD KEY `property_id` (`property_id`);
ALTER TABLE `rentals_savedproperty` ADD KEY `property_id` (`property_id`);
ALTER TABLE `rentals_report` ADD KEY `property_id` (`property_id`);
ALTER TABLE `rentals_adminmessage` ADD KEY `created_by_id` (`created_by_id`);

-- =====================================================
-- AUTO INCREMENT VALUES
-- =====================================================

ALTER TABLE `auth_group` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `auth_group_permissions` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `auth_permission` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `auth_user` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `auth_user_groups` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `auth_user_user_permissions` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `django_admin_log` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `django_content_type` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `django_migrations` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_userprofile` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_property` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_propertyownership` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_propertyrental` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_studentpropertyrental` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_studentproperty` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_payment` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_transaction` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_propertyvisit` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_propertyinquiry` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_savedproperty` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_report` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `rentals_adminmessage` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

COMMIT;
