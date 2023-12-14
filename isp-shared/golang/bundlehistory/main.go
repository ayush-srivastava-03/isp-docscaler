package bundlehistory

import (
	"fmt"
	"isp/clickhouse"
	"isp/clickhouse/migrations"
	"time"
)

type BundleHistory struct {
	db     *clickhouse.Connection
	module string
}

type BundleHistoryObject struct {
	BundleId  string     `json:"bundleId" db:"bundle_id"`
	Timestamp *time.Time `json:"timestamp" db:"timestamp"`
	Source    string     `json:"source" db:"source"`
	Severity  string     `json:"severity" db:"severity"`
	Message   string     `json:"message" db:"message"`
}

var table = migrations.PARSER_DATABASE_NAME + "." + migrations.BUNDLE_HISTORY_TABLE_BUFFER

func Init(module string, db *clickhouse.Connection) (*BundleHistory, error) {
	return &BundleHistory{
		db:     db,
		module: module,
	}, nil
}

func (bh *BundleHistory) publish(severity, bundleId, message string, ts ...time.Time) error {
	t := time.Now()
	if len(ts) != 0 {
		t = ts[0]
	}

	tx, err := bh.db.Begin()
	if err != nil {
		return err
	}

	if _, err := tx.Exec(fmt.Sprintf(`
		INSERT INTO %s (
			bundle_id,
			timestamp,
			source,
			severity,
			message
		) VALUES (?, ?, ?, ?, ?)
	`, table),
		bundleId,
		t,
		bh.module,
		severity,
		message,
	); err != nil {
		return err
	}

	return tx.Commit()
}

func (b *BundleHistory) Info(bid, msg string, ts ...time.Time) error {
	return b.publish("info", bid, msg, ts...)
}

func (b *BundleHistory) Warn(bid, msg string, ts ...time.Time) error {
	return b.publish("warning", bid, msg, ts...)
}

func (b *BundleHistory) Error(bid, msg string, ts ...time.Time) error {
	return b.publish("error", bid, msg, ts...)
}
