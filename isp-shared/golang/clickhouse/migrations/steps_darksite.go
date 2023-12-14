package migrations

import "fmt"

var StepsDarksite = []string{
	fmt.Sprintf(`CREATE DATABASE IF NOT EXISTS %s`, PARSER_DATABASE_NAME),
	fmt.Sprintf(`CREATE DATABASE IF NOT EXISTS %s`, CATALOG_DATABASE_NAME),

	// Parser

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
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
		ENGINE = ReplacingMergeTree(version)
		PARTITION BY (system_type, toYYYYMM(timestamp))
		ORDER BY (system_type, system_id, timestamp, source, component, severity, message, raid_processor, event)
	`, PARSER_DATABASE_NAME, LOGS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
			bundle_id UUID NOT NULL,
			system_id String NOT NULL,
			system_type String NOT NULL,
			object_type String NOT NULL,
			data String NOT NULL,
			hash UInt64 DEFAULT sipHash64(data)
		)
		ENGINE = ReplacingMergeTree(hash)
		PARTITION BY (system_type, object_type)
		ORDER BY (system_type, system_id, bundle_id, object_type, hash)
	`, PARSER_DATABASE_NAME, OBJECTS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
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
		ENGINE = MergeTree()
		ORDER BY (query_id)
	`, PARSER_DATABASE_NAME, LOG_QUERIES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, OBJECTS_TABLE_BUFFER, PARSER_DATABASE_NAME, OBJECTS_TABLE, PARSER_DATABASE_NAME, OBJECTS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, LOGS_TABLE_BUFFER, PARSER_DATABASE_NAME, LOGS_TABLE, PARSER_DATABASE_NAME, LOGS_TABLE),

	fmt.Sprintf(`
        CREATE TABLE IF NOT EXISTS %s.%s (
            id UUID NOT NULL,
            type Int32 NOT NULL,
            name String NOT NULL,
            description String,
            user_id String NOT NULL,
            public UInt8 DEFAULT 0, // boolean
            timestamp DateTime('UTC') DEFAULT now(),
            data String NOT NULL
        )
        ENGINE = MergeTree()
        ORDER BY (id)
    `, PARSER_DATABASE_NAME, USER_DATA_TABLE),

	// Bundle history
	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
			bundle_id UUID NOT NULL,
			timestamp DateTime DEFAULT NOW(),
			source String,
			severity enum('info','warning','error') NOT NULL DEFAULT 'info',
			message String NOT NULL
		)
		ENGINE = MergeTree()
		PARTITION BY toYYYYMM(timestamp)
		ORDER BY (bundle_id)
		TTL timestamp + INTERVAL 1 MONTH
	`, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s AS %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE_BUFFER, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE, PARSER_DATABASE_NAME, BUNDLE_HISTORY_TABLE),

	// Catalog

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
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
		ENGINE = ReplacingMergeTree()
		PARTITION BY (system_type, toYYYYMM(created))
		ORDER BY (system_type, bundle_type, support_case, platform, created)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
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
		ENGINE = ReplacingMergeTree()
		PARTITION BY (toYear(timestamp))
		ORDER BY (asset_id);
	`, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
			customer_id String NOT NULL,
			customer_name String NOT NULL,
			timestamp DateTime('UTC') NOT NULL,
			sfdc_source Enum8 ('ddn' = 0, 'tintri' = 1) NOT NULL
		)
		ENGINE = ReplacingMergeTree()
		PARTITION BY (toYear(timestamp))
		ORDER BY (customer_id);
	`, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
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
		ENGINE = ReplacingMergeTree()
		PARTITION BY (toYear(timestamp))
		ORDER BY (case_number);
	`, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE_BUFFER, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s  as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE_BUFFER, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE, CATALOG_DATABASE_NAME, CATALOG_ASSETS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s  as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE_BUFFER, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE, CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s  as %s.%s
		ENGINE = Buffer(%s, %s, 4, 5, 15, 100000, 1000000, 10000000, 100000000)
	`, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE_BUFFER, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE, CATALOG_DATABASE_NAME, CATALOG_CASES_TABLE),

	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.%s (
			system_id String NOT NULL,
			label String NOT NULL
		)
		ENGINE = ReplacingMergeTree()
		ORDER BY (system_id, label)
	`, CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE),

	// Bundle tags and their materialized views
	fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.tags (
			bundle_id UUID NOT NULL,
			tag String NOT NULL,
			value String NOT NULL
		)
		ENGINE = ReplacingMergeTree()
		PARTITION BY (tag)
		ORDER BY (bundle_id, tag)
	`, CATALOG_DATABASE_NAME),

	// tags.system_name (SFA)
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_system_name
		TO %s.tags
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
		CATALOG_DATABASE_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
	),

	// tags.uuid (SFA)
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_sfa_uuid
		TO %s.tags
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
		CATALOG_DATABASE_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
	),

	// tags.cluster_name
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_cluster_name
		TO %s.tags
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
		CATALOG_DATABASE_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
	),

	// tags.ue_customer_name
	fmt.Sprintf(`
		CREATE MATERIALIZED VIEW IF NOT EXISTS %s.tags_ue_customer_name
		TO %s.tags
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
		CATALOG_DATABASE_NAME,
		CATALOG_DATABASE_NAME,
		PARSER_DATABASE_NAME, OBJECTS_TABLE,
	),

	// TODO: Should we convert to materialized view?
	// CREATE MATERIALIZED VIEW IF NOT EXISTS %s.%s ON CLUSTER %s
	// ENGINE = ReplicatedReplacingMergeTree('/clickhouse/tables/{cluster}/{shard}/{database}.{table}', '{replica}')
	// ORDER BY (bundle_id)
	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s
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
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
		CATALOG_DATABASE_NAME,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s AS (
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
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s AS (
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
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
	),

	fmt.Sprintf(`
		CREATE VIEW IF NOT EXISTS %s.%s AS (
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
	`, CATALOG_DATABASE_NAME, CATALOG_BUNDLES_BY_UNIQUE_SYSTEM_VIEW,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLES_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_CUSTOMERS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_LABELS_TABLE,
		CATALOG_DATABASE_NAME, CATALOG_BUNDLE_TAGS_VIEW,
	),
}
