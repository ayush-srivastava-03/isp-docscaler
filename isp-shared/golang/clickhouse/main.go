package clickhouse

// Set of helpers for better experience with clickhouse

import (
	"fmt"
	"time"

	_ "github.com/ClickHouse/clickhouse-go"
	"github.com/mailru/dbr"

	"isp/clickhouse/migrations"
	"isp/config"
	"isp/deployment"
	"isp/log"
)

var (
	CLICKHOUSE_ADDRESS = config.Get("CLICKHOUSE_ADDRESS", "tcp://localhost:9000")

	// As per https://github.com/ClickHouse/clickhouse-go/issues/336
	CLICKHOUSE_CONN_LIFETIME = config.GetInt("CLICKHOUSE_CONN_LIFETIME", 15)
)

type Connection struct {
	*dbr.Connection
}

func CreateConnection(addr ...string) (*Connection, error) {
	url := CLICKHOUSE_ADDRESS
	if len(addr) > 0 {
		url = addr[0]
	}

	if !deployment.IsDarkSite() && migrations.CLICKHOUSE_CLUSTER_NAME == "" {
		return nil, fmt.Errorf("Cloud deployment ENV is missing: CLICKHOUSE_CLUSTER_NAME is not defined")
	}

	conn, err := dbr.Open("clickhouse", url, nil)
	if err != nil {
		return nil, err
	}

	if err := conn.Ping(); err != nil {
		return nil, err
	}

	conn.SetConnMaxLifetime(time.Duration(CLICKHOUSE_CONN_LIFETIME) * time.Minute)

	return &Connection{conn}, nil
}

func (conn *Connection) RunMigration() error {
	steps := migrations.Steps
	if deployment.IsDarkSite() {
		log.Msg.Info("Detected darksite deployment. Using simple database schema")
		steps = migrations.StepsDarksite
	}

	log.Msg.Infof("Running clickhouse migration (total steps: %d)", len(steps))
	for i, step := range steps {
		if _, err := conn.Exec(step); err != nil {
			return fmt.Errorf("Migration step %d: %v", i, err)
		}
	}

	if deployment.IsDarkSite() {
		if err := conn.importLogQueries(); err != nil {
			return fmt.Errorf("Import log queries: %v", err)
		}
	}

	return nil
}

func (conn *Connection) importLogQueries() error {
	queries := migrations.LogQueries

	query := conn.NewSession(nil).SelectBySql(
		fmt.Sprintf("SELECT query_id from %s.%s LIMIT 10000", migrations.PARSER_DATABASE_NAME, migrations.LOG_QUERIES_TABLE),
	)

	data := []string{}
	if _, err := query.Load(&data); err != nil {
		return err
	}

	toImport := map[string]migrations.LogQuery{}
	for id, q := range queries {
		if !inArray(data, id) {
			toImport[id] = q
		}
	}

	tx, err := conn.Begin()
	if err != nil {
		return err
	}

	iq, err := tx.Prepare(fmt.Sprintf(`
		INSERT INTO %s.%s (
			query_id,
			name,
			description,
			severity,
			user_id,
			autorun,
			public,
			timestamp,
			query
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, migrations.PARSER_DATABASE_NAME, migrations.LOG_QUERIES_TABLE))
	if err != nil {
		tx.Rollback()
		return err
	}

	for id, q := range toImport {
		if _, err := iq.Exec(
			id,
			q.Name,
			q.Description,
			q.Severity,
			"dark_site",
			1,
			1,
			time.Now(),
			q.Query,
		); err != nil {
			return err
		}
	}

	return tx.Commit()
}

func inArray(s []string, val string) bool {
	for _, v := range s {
		if v == val {
			return true
		}
	}

	return false
}
