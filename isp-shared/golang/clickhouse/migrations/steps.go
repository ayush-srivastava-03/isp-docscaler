package migrations

import "fmt"

var Steps = []string{
	fmt.Sprintf(`CREATE DATABASE IF NOT EXISTS %s ON CLUSTER %s`, PARSER_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME),
	fmt.Sprintf(`CREATE DATABASE IF NOT EXISTS %s ON CLUSTER %s`, CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME),
	fmt.Sprintf(`CREATE DATABASE IF NOT EXISTS %s ON CLUSTER %s`, REPORTS_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME),

	// Parser

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			bundle_id UUID NOT NULL,
			system_id String NOT NULL,
			system_type String NOT NULL,
			timestamp DateTime64(6, 'UTC') NOT NULL,
			source String,
			component String,
			severity String,
			message String NOT NULL,
			raid_processor String,
			event String,
			sequence String,
			version UInt32 DEFAULT 4294967295 - toUInt32(now()) // Inverse ReplacingMergeTree logic: oldest record is kept, newer is removed
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}', version)
		PARTITION BY (system_type, toYYYYMM(timestamp))
		ORDER BY (system_type, system_id, timestamp, source, component, severity, message, raid_processor, event, sequence)
	`, PARSER_DATABASE_NAME, LOGS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(system_id))
	`, PARSER_DATABASE_NAME, LOGS_TABLE, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, LOGS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, LOGS_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			bundle_id UUID NOT NULL,
			system_id String NOT NULL,
			system_type String NOT NULL,
			object_type String NOT NULL,
			data String NOT NULL,
			hash UInt64 DEFAULT sipHash64(data)
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY (system_type, object_type)
		ORDER BY (system_type, system_id, bundle_id, object_type, hash)
	`, PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(system_id))
	`, PARSER_DATABASE_NAME, OBJECTS_TABLE, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			query_id UUID NOT NULL,
			name String NOT NULL,
			description String,
			severity Enum8 ('info' = 0, 'warning' = 1, 'error' = 2) NOT NULL,
			user_id String NOT NULL,
			autorun UInt8 DEFAULT 0, // boolean
			public UInt8 DEFAULT 0, // boolean
			timestamp DateTime('UTC') DEFAULT now(),
			query String NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		ORDER BY (query_id)
	`, PARSER_DATABASE_NAME, LOG_QUERIES_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(user_id))
	`, PARSER_DATABASE_NAME, LOG_QUERIES_TABLE, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, LOG_QUERIES_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, LOG_QUERIES_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, OBJECTS_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, OBJECTS_TABLE, PARSER_DATABASE_NAME, OBJECTS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, LOGS_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, LOGS_TABLE, PARSER_DATABASE_NAME, LOGS_TABLE),

	fmt.Sprintf(`
        CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
            id UUID NOT NULL,
            type Int32 NOT NULL,
            name String NOT NULL,
            description String,
            user_id String NOT NULL,
            public UInt8 DEFAULT 0, // boolean
            timestamp DateTime('UTC') DEFAULT now(),
            data String NOT NULL
        )
        ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
        ORDER BY (id)
    `, PARSER_DATABASE_NAME, USER_DATA_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
        CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
        ENGINE = Distributed('%s', %s, %s, sipHash64(user_id))
    `, PARSER_DATABASE_NAME, USER_DATA_TABLE, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, USER_DATA_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, USER_DATA_TABLE_LOCAL),

	// Bundle history
	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			bundle_id UUID NOT NULL,
			timestamp DateTime DEFAULT NOW(),
			source String,
			severity enum('info','warning','error') NOT NULL DEFAULT 'info',
			message String NOT NULL
		)
		ENGINE = ReplicatedMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY toYYYYMM(timestamp)
		ORDER BY (bundle_id)
		TTL timestamp + INTERVAL 1 MONTH
	`, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(bundle_id))
	`, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE),

	// KB
	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			object_type String NOT NULL,
			data String NOT NULL
		)
		ENGINE = ReplicatedMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY object_type
		ORDER BY object_type
	`, PARSER_DATABASE_NAME, KB_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(object_type)) // TODO: perhaps distribution is not really needed here
	`, PARSER_DATABASE_NAME, KB_TABLE, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, KB_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, KB_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, KB_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, PARSER_DATABASE_NAME, KB_TABLE_LOCAL, PARSER_DATABASE_NAME, KB_TABLE_LOCAL),

	// Catalog

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			bundle_id UUID NOT NULL,
			bundle_version String NOT NULL,
			bundle_type String NOT NULL,
			bundle_size UInt64 NOT NULL,
			customer_id String NOT NULL,
			system_type String NOT NULL,
			system_id String NOT NULL,
			support_case String DEFAULT '',
			platform String DEFAULT '',
			s3_bucket String NOT NULL,
			s3_key String NOT NULL,
			created DateTime64(3, 'UTC') NOT NULL,
			sender_ip String DEFAULT '',
			uploaded DateTime64(3, 'UTC') NOT NULL,
			fingerprint String NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY (system_type, toYYYYMM(created))
		ORDER BY (system_type, bundle_type, support_case, platform, created)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(system_id))
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			timestamp DateTime('UTC') NOT NULL,
			asset_id String NOT NULL,
			asset_number String,
			system_id String,
			system_name String,
			serial_00 String,
			serial_01 String,
			customer_id String NOT NULL,
			product_code String,
			sfdc_source Enum8 ('ddn' = 0, 'tintri' = 1) NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY (toYear(timestamp))
		ORDER BY (asset_id);
	`, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(system_id))
	`, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			customer_id String NOT NULL,
			customer_name String NOT NULL,
			timestamp DateTime('UTC') NOT NULL,
			sfdc_source Enum8 ('ddn' = 0, 'tintri' = 1) NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY (toYear(timestamp))
		ORDER BY (customer_id);
	`, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(customer_id))
	`, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			case_id String NOT NULL,
			case_number String NOT NULL,
			customer_id String NOT NULL,
			contact_email String,
			contact_fax String,
			contact_mobile String,
			contact_phone String,
			contact_name String,
			case_subject String,
			timestamp DateTime('UTC') NOT NULL,
			sfdc_source Enum8 ('ddn' = 0, 'tintri' = 1) NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY (toYear(timestamp))
		ORDER BY (case_number);
	`, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(case_number))
	`, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE_LOCAL),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE_BUFFER, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s (
			system_id String NOT NULL,
			label String NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		ORDER BY (system_id, label)
	`, CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(system_id))
	`, CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE_LOCAL, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE_LOCAL),

	// Bundle tags and their materialized views
	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.tags_local ON CLUSTER %s (
			bundle_id UUID NOT NULL,
			tag String NOT NULL,
			value String NOT NULL
		)
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		PARTITION BY (tag)
		ORDER BY (bundle_id, tag)
	`, CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME),

	// tags.system_name (SFA)
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_system_name_local ON CLUSTER %s
		TO %s.tags_local
		AS (
			SELECT DISTINCT
				bundle_id,
				'system_name' AS tag,
				JSONExtractString(data, 'Name') AS value
			FROM %s.%s
			WHERE
			system_type='sfa' AND object_type = 'StorageSystem' AND notEmpty(value)
		)
	`,
		CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL,
	),

	// tags.uuid (SFA)
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_sfa_uuid_local ON CLUSTER %s
		TO %s.tags_local
		AS (
			SELECT DISTINCT
				bundle_id,
				'sfa_uuid' AS tag,
				JSONExtractString(data, 'uuid') AS value
			FROM %s.%s
			WHERE
			system_type='sfa' AND object_type = 'BundleInfo' AND notEmpty(value)
		)
	`,
		CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL,
	),

	// tags.cluster_name
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_cluster_name_local ON CLUSTER %s
		TO %s.tags_local
		AS (
			SELECT DISTINCT
				bundle_id,
				'cluster_name' AS tag,
				JSONExtractString(data, 'ClusterName') AS value
			FROM %s.%s
			WHERE
			object_type = 'BundleInfo' AND notEmpty(value)
		)
	`,
		CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL,
	),

	// tags.ue_customer_name
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_ue_customer_name_local ON CLUSTER %s
		TO %s.tags_local
		AS (
			SELECT DISTINCT
				bundle_id,
				'ue_customer_name' AS tag,
				JSONExtractString(data, 'Customer') AS value
			FROM %s.%s
			WHERE
			object_type = 'BundleInfo' AND notEmpty(value)
		)
	`,
		CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE_LOCAL,
	),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.tags ON CLUSTER %s AS %s.tags_local
		ENGINE = Distributed('%s', %s, tags_local, sipHash64(bundle_id))
	`,
		CATALOG_DATABASE_NAME, CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME,
		CLICKHOUSE_CLUSTER_NAME, CATALOG_DATABASE_NAME,
	),

	// TODO: Should we convert to materialized view?
	// CREATE MATERIALIZED VIEW IF NOT EXISTS %s.%s ON CLUSTER %s
	// ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
	// ORDER BY (bundle_id)
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s
		// ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		// ORDER BY (bundle_id)
		// POPULATE
		AS (
			SELECT
				bundle_id,
				CAST(
				   (
					   // tag names
					   arrayMap(x -> (x[1]), groupUniqArray(16)([tag, value])),
					   // tag values
					   arrayMap(x -> (x[2]), groupUniqArray(16)([tag, value]))
				   ),
				   'Map(String, String)'
				) AS tags
			   // tag_name, value is required per each union
			   FROM %s.tags
			   GROUP BY bundle_id
		)
	`,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			SELECT DISTINCT
				bundles.bundle_id AS bundle_id,
				bundle_version,
				bundle_type,
				bundle_size,

				bundles.customer_id AS customer_id,
				bundles.system_id AS system_id,

				system_type,
				support_case,
				platform,
				s3_bucket,
				s3_key,
				sender_ip,
				created,
				uploaded,
				fingerprint,
				labels.label AS label,
				if(customers.customer_name = '', 'Unknown', customers.customer_name) AS customer_name,
				tags.tags AS tags,

				// compatibility with aggregated views
				1 AS count
			FROM %s.%s AS bundles

			GLOBAL LEFT JOIN %s.%s AS customers ON customers.customer_id = bundles.customer_id

			LEFT JOIN %s.%s AS labels ON labels.system_id = bundles.system_id
			LEFT JOIN %s.%s AS tags ON tags.bundle_id = bundles.bundle_id
		)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_VIEW, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
            SELECT DISTINCT
				agg_data.bundle_id AS bundle_id,
				bundle_version,
				bundle_type,
				bundle_size,

				bundles.customer_id AS customer_id,
				bundles.system_id AS system_id,
				bundles.system_type AS system_type,

				support_case,
				platform,
				s3_bucket,
				s3_key,
				sender_ip,
				bundles.created AS created,
				uploaded,
				fingerprint,
				labels.label AS label,
				if(customers.customer_name = '', 'Unknown', customers.customer_name) AS customer_name,
				agg_data.tags AS tags,
				count
            FROM (
                SELECT
                    argMax(bundle_id, created) AS bundle_id,
                    system_id AS system_id,
                    system_type AS system_type,
                    argMax(tags, created) AS tags,
                    count() AS count
                FROM %s.%s bundles
                LEFT JOIN %s.%s AS tags ON tags.bundle_id = bundles.bundle_id
                GROUP BY system_id, system_type
            ) agg_data

			LEFT JOIN %s.%s bundles ON bundles.bundle_id = agg_data.bundle_id

			LEFT JOIN  %s.%s AS customers ON customers.customer_id = bundles.customer_id

			LEFT JOIN  %s.%s AS labels ON labels.system_id = bundles.system_id

		)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_SYSTEM_VIEW, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
            SELECT DISTINCT
				agg_data.bundle_id AS bundle_id,
				bundle_version,
				bundle_type,
				bundle_size,

				bundles.customer_id AS customer_id,
				bundles.system_id AS system_id,
				bundles.system_type AS system_type,

				support_case,
				platform,
				s3_bucket,
				s3_key,
				sender_ip,
				bundles.created AS created,
				uploaded,
				fingerprint,
				labels.label AS label,
				if(customers.customer_name = '', 'Unknown', customers.customer_name) AS customer_name,
				tags.tags AS tags,
				count
            FROM (
                SELECT
                    argMax(bundle_id, created) AS bundle_id,
                    system_id AS system_id,
                    system_type AS system_type,
                    count() AS count
                FROM %s.%s bundles
                GROUP BY system_id, system_type
            ) agg_data

			LEFT JOIN %s.%s bundles ON bundles.bundle_id = agg_data.bundle_id
			LEFT JOIN  %s.%s AS customers ON customers.customer_id = bundles.customer_id
			LEFT JOIN  %s.%s AS labels ON labels.system_id = bundles.system_id
			LEFT JOIN %s.%s AS tags ON tags.bundle_id = bundles.bundle_id

		)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
	),

	// Reports
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.%s ON CLUSTER %s
		ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
		ORDER BY (serial_number, timestamp)
		POPULATE
		AS (
			SELECT DISTINCT
			dd.bundle_id AS bundle_id,
			JSONExtractString(dd.data, 'SerialNumber') AS serial_number,
			JSONExtractString(dd.data, 'VendorID') AS vendor_id,
			JSONExtractString(dd.data, 'ProductID') AS product_id,
			JSONExtractString(dd.data, 'ProductRevision') AS product_revision,
			JSONExtractString(dd.data, 'BlockSize') AS block_size,

			multiIf(block_size = 'BLOCK_512', 512, block_size = 'BLOCK_4096', 4096, block_size = 'BLOCK_4K', 4096, 0) AS block_size_bytes,
			(toInt64OrDefault(JSONExtractString(dd.data, 'RawCapacity'), toInt64(0)) * block_size_bytes) AS raw_capacity,

			JSONExtractString(dd.data, 'RotationSpeed') AS disk_speed,

			if(disk_speed = 'DISK_SPEED_SSD' AND JSONExtractString(dd.data, 'SMARTAttributes', 1) = 'SSD Life Left' , JSONExtractInt(dd.data, 'SMARTValues', 1), -1) AS ssd_life_left,

			JSONExtractString(dd.data, 'HealthState') AS health_state,
			JSONExtractString(dd.data, 'HealthStateReason') AS health_state_reason,

			cb.created AS timestamp,
			cb.customer_id AS customer_id,
			cb.customer_name AS customer_sfdc,
			cb.system_id as system_id,
			cb.platform

			FROM data.bundle_objects dd
			JOIN %s.%s cb ON dd.bundle_id = cb.bundle_id
			WHERE
			dd.object_type = 'DiskDrive'
		)
	`, REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW_LOCAL, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_VIEW,
	),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s ON CLUSTER %s AS %s.%s
		ENGINE = Distributed('%s', %s, %s, sipHash64(system_id))
	`, REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW, CLICKHOUSE_CLUSTER_NAME, REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW_LOCAL, CLICKHOUSE_CLUSTER_NAME, REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW_LOCAL),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			SELECT DISTINCT
				bundle_id,
				timestamp,
				serial_number,
				vendor_id,
				product_id,
				product_revision,
				disk_speed,
				raw_capacity,
				ssd_life_left,
				health_state,
				health_state_reason,
				customer_id,
				customer_sfdc,
				system_id,
				platform
			FROM %s.%s
			WHERE (timestamp, serial_number) GLOBAL IN (
				SELECT distinct max(timestamp) as timestamp, serial_number FROM %s.%s
				GROUP BY serial_number
			)
		)
	`, REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW_BY_SERIAL, CLICKHOUSE_CLUSTER_NAME,
		REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW,
		REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW,
	),

	// System configuirations
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			SELECT DISTINCT
					c.bundle_id AS bundle_id,
					c.system_id AS system_id,
					c.customer_id AS customer_id,
					c.customer_name AS customer_sfdc,
					c.created AS timestamp,
					c.platform AS platform,
					rdd.capacity AS capacity,
					ss.config_date AS config_date,
					ss.disk_enclosure_config AS disk_enclosure_config
					// si.enclosure_config AS enclosure_config

			FROM %s.%s c

			LEFT JOIN (
				SELECT DISTINCT
					bundle_id,
					sum(raw_capacity) AS capacity
				FROM %s.%s
				GROUP BY bundle_id
			) rdd ON rdd.bundle_id = c.bundle_id

			LEFT JOIN (
				SELECT DISTINCT
					bundle_id,
					parseDateTimeBestEffortOrNull(JSONExtractString(data, 'ConfigDate')) AS config_date,
					JSONExtractString(data, 'DiskEnclosureConfiguration') AS disk_enclosure_config
				FROM %s.%s
				WHERE object_type = 'StorageSystem'
				GROUP BY bundle_id, config_date, disk_enclosure_config
			) ss ON ss.bundle_id = c.bundle_id

			// LEFT JOIN (
			// 		SELECT DISTINCT
			// 		bundle_id,
			// 		JSONExtractString(data, 'enclosures') AS enclosure_config
			// 		FROM %s.%s
			// 		WHERE system_type = 'sfa' AND object_type = 'SystemInfo'
			// 		GROUP BY bundle_id, enclosure_config
			// ) si ON si.bundle_id = c.bundle_id

			WHERE c.system_type = 'sfa' AND capacity > 0
		)
	`, REPORTS_DATABASE_NAME, REPORTS_SYSTEM_CONFIGURATIONS_VIEW, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_VIEW,
		REPORTS_DATABASE_NAME, REPORTS_DISK_DRIVES_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			SELECT DISTINCT
				bundle_id,
				system_id,
				customer_id,
				customer_sfdc,
				timestamp,
				platform,
				capacity,
				config_date,
				disk_enclosure_config
				// enclosure_config
			FROM %s.%s
			WHERE (timestamp, system_id) GLOBAL IN (
				SELECT DISTINCT max(created) as timestamp, system_id FROM %s.%s
				WHERE system_type = 'sfa'
				GROUP BY system_id
			)
		)
	`, REPORTS_DATABASE_NAME, REPORTS_SYSTEM_CONFIGURATIONS_VIEW_BY_SYSTEM_ID, CLICKHOUSE_CLUSTER_NAME,
		REPORTS_DATABASE_NAME, REPORTS_SYSTEM_CONFIGURATIONS_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
	),

	// Unknown customers
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			SELECT DISTINCT
				b.bundle_id AS bundle_id,
				b.system_id AS system_id,
				b.customer_id AS customer_id,
				b.customer_name AS customer_name,
				b.bundle_type AS bundle_type,
				b.support_case AS support_case,
				if(c.customer_id = '', 'unknown', c.customer_id) AS case_customer_id,
				if(cust.customer_name = '', 'Unknown', cust.customer_name) AS case_customer_name

			FROM %s.%s b
			LEFT JOIN %s.%s c ON c.case_number = b.support_case
			LEFT JOIN %s.%s cust ON cust.customer_id = c.customer_id
		)
	`, REPORTS_DATABASE_NAME, REPORTS_UNKNOWN_CUSTOMERS_VIEW, CLICKHOUSE_CLUSTER_NAME,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
	),

	// Adopted customers
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
				SELECT DISTINCT
				if(customer_id = 'unknown', case_customer_id, 'unknown') AS customer_id,
				if(customer_name = 'Unknown', case_customer_name, 'Unknown') AS customer_name,
				bundle_type,
				count() AS count
			FROM %s.%s
			WHERE bundle_type != 'manufacturing'
			GROUP BY
				customer_id,
				customer_name,
				bundle_type
		)
	`,
		REPORTS_DATABASE_NAME, REPORTS_ADOPTED_CUSTOMERS_VIEW, CLICKHOUSE_CLUSTER_NAME,
		REPORTS_DATABASE_NAME, REPORTS_UNKNOWN_CUSTOMERS_VIEW,
	),

	// SFA Summary report
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			WITH
			ct AS (
			SELECT
				bundle_id,
				JSONExtractString(data, 'VendorEquipmentType') AS platform,
				JSONExtractString(data, 'FWRelease') AS release
			FROM %s.%s
			WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='sfa') AND object_type = 'Controller'
			),
			en AS (
				SELECT
				bundle_id,
				max(cnt) AS count,
				argMax(type, cnt) AS type,
				argMax(model, cnt) AS model
			FROM (
				SELECT
					bundle_id,
					COUNT() AS cnt,
					JSONExtractString(data, 'Type') AS type,
					JSONExtractString(data, 'Model') AS model
				FROM %s.%s
				WHERE
					bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='sfa') AND object_type = 'Enclosure' AND type = 'TYPE_DISK'
				GROUP BY bundle_id, type, model
			)
				GROUP BY bundle_id
			)
			SELECT DISTINCT
				c.bundle_id AS bundle_id,
				c.created AS timestamp,
				c.system_id AS system_id,
				c.customer_id AS customer_id,
				c.customer_name AS customer_name,
				toJSONString(c.tags) AS tags_json,
				ct.platform AS platform,
				ct.release AS release_version,
				en.count AS enclosure_count,
				en.model AS enclosure_model
			FROM %s.%s c


			LEFT JOIN ct ON ct.bundle_id = c.bundle_id
			LEFT JOIN en ON en.bundle_id = c.bundle_id

			WHERE c.system_type='sfa'
		)
	`,
		REPORTS_DATABASE_NAME, REPORTS_SFA_REPORT_VIEW, CLICKHOUSE_CLUSTER_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
	),

	// EXA Summary report
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			WITH
			ev AS (
			  SELECT DISTINCT
				bundle_id,
				JSONExtractString(data, 'exascalerVersion') AS version,
				JSONExtractString(data, 'stonithType') AS stonith_type
			  FROM %s.%s
			  WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='exascaler') AND object_type = 'Node'
			),
			v AS (
				SELECT
					  bundle_id,
					  CAST(
						 (
						   arrayMap(x -> (x[2]), groupUniqArray(16)([JSONExtractString(data, 'version'), JSONExtractString(data, 'name')])),
						   arrayMap(x -> (x[1]), groupUniqArray(16)([JSONExtractString(data, 'version'), JSONExtractString(data, 'name')]))
						 ),
						 'Map(String, String)'
					  ) AS versions
				FROM %s.%s
				WHERE
					  bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='exascaler') AND object_type = 'SoftwareVersion'
				GROUP BY bundle_id
			)
			SELECT DISTINCT
				c.bundle_id AS bundle_id,
				c.system_id AS system_id,
				c.created AS timestamp,
				c.customer_id AS customer_id,
				c.customer_name AS customer_name,
				toJSONString(c.tags) AS tags_json,
				ev.version AS version,
				ev.stonith_type AS stonith_type,
				v.versions['Exascaler'] AS full_version,
				v.versions['Lustre'] AS lustre_version,
				v.versions['Kernel'] AS kernel_version,
				v.versions['Linux'] AS linux_version
			FROM %s.%s c

			LEFT JOIN ev ON ev.bundle_id = c.bundle_id
			LEFT JOIN v ON v.bundle_id = c.bundle_id

			WHERE c.system_type='exascaler'
		)
	`,
		REPORTS_DATABASE_NAME, REPORTS_EXA_REPORT_VIEW, CLICKHOUSE_CLUSTER_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
	),

	// Nightly systems health report
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s ON CLUSTER %s AS (
			WITH
			// SFA failures total
			sfaf AS (
				SELECT DISTINCT ON (bundle_id)
				bundle_id,
				COUNT() AS count
			  FROM %s.%s
			  WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='sfa')
				AND object_type IN ('Connector', 'DiskSlot', 'Enclosure', 'Expander', 'Fan', 'InternalDiskDrive', 'PowerSupply', 'UPS')
				AND JSONExtractBool(data, 'Fault') = true
			  GROUP BY bundle_id
			),
			// Exascaler failures total
			exaf AS (
				SELECT DISTINCT ON (bundle_id)
				bundle_id,
				arraySum(
					v -> JSONExtractUInt(v, 'count'),
					arrayFilter(
						v -> JSONExtractString(v, 'health') IN ('HEALTH_STATE_ERROR', 'HEALTH_STATE_CRITICAL'),
						JSONExtractArrayRaw(data, 'healthStats')
					)
				) AS count
			  FROM %s.%s
			  WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='exascaler') AND object_type = 'ParserData'
			),
			// Exascaler name and version
			exan AS (
				SELECT DISTINCT ON (bundle_id)
				bundle_id,
				JSONExtractString(data, 'filesystemName') AS name,
				JSONExtractString(data, 'exascalerVersion') AS version
			  FROM %s.%s
			  WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='exascaler') AND object_type = 'Node'
			),
			// SFA Name
			sfan AS (
				SELECT DISTINCT ON (bundle_id)
				bundle_id,
				JSONExtractString(data, 'Name') AS name
			  FROM %s.%s
			  WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='sfa') AND object_type = 'StorageSystem'
			),
			// SFA version
			sfav AS (
				SELECT DISTINCT ON (bundle_id)
				bundle_id,
				JSONExtractString(data, 'FirmwareVersion') AS version
			  FROM %s.%s
			  WHERE
				bundle_id IN (SELECT bundle_id FROM %s.%s WHERE system_type='sfa') AND object_type = 'Enclosure' AND JSONExtractString(data, 'Type') = 'TYPE_CONTROLLER'
			)
			SELECT
				c.bundle_id AS bundle_id,
				c.system_id AS system_id,
				c.bundle_type AS bundle_type,
				c.customer_id AS customer_id,
				if (c.tags['ue_customer_name'] != '', c.tags['ue_customer_name'], c.customer_name) AS customer_name,
				c.created AS timestamp,
				c.system_type AS system_type,
				if (system_type = 'sfa', sfan.name, exan.name) AS system_name,
				if (system_type = 'sfa', sfaf.count, exaf.count) AS errors,
				if (system_type = 'sfa', sfav.version, exan.version) AS version,
				l.label AS label
			FROM %s.%s c
			LEFT JOIN exaf ON exaf.bundle_id = c.bundle_id
			LEFT JOIN sfaf ON sfaf.bundle_id = c.bundle_id
			LEFT JOIN sfan ON sfan.bundle_id = c.bundle_id
			LEFT JOIN exan ON exan.bundle_id = c.bundle_id
			LEFT JOIN sfav ON sfav.bundle_id = c.bundle_id
			LEFT JOIN %s.%s l ON l.system_id = c.system_id
		)
	`,
		REPORTS_DATABASE_NAME, REPORTS_SYSTEM_HEALTH_VIEW, CLICKHOUSE_CLUSTER_NAME,

		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
	),
}
