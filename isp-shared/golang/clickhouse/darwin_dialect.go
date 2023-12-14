package clickhouse

type clickhouseDialect struct{}

func (m clickhouseDialect) CreateTableSQL() string {
	return `CREATE TABLE IF NOT EXISTS darwin_migrations
				(
					version        Float64 NOT NULL,
					description    String NOT NULL,
					checksum       String NOT NULL,
					applied_at     UInt16 NOT NULL,
					execution_time UInt64 NOT NULL,
					PRIMARY KEY    (version)
				)
				ENGINE = MergeTree();`
}

func (m clickhouseDialect) InsertSQL() string {
	return `INSERT INTO darwin_migrations (
					version,
					description,
					checksum,
					applied_at,
					execution_time
			) VALUES (?, ?, ?, ?, ?);`
}

func (m clickhouseDialect) AllSQL() string {
	return `SELECT
				version,
				description,
				checksum,
				applied_at,
				execution_time
			FROM
				darwin_migrations
			ORDER BY version ASC;`
}
