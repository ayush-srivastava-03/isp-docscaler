package config

import (
	"fmt"
	"isp/log"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

var envPaths = []string{".env", "/.env", "/root/.env", "~/.env"}

func init() {
	// Try to load files sequentially, until first found
	for _, fname := range envPaths {
		if err := godotenv.Load(fname); err == nil {
			return
		}
	}

	log.Msg.Debugf(".env files not found (lookup paths: %s)", strings.Join(envPaths, ", "))
}

// Get config value as a string
// Value is taken in following order:
// 1. Enviromental variable of the same name
// 2. .env file
// 3. Default value
func Get(name string, def ...string) string {
	val, _ := os.LookupEnv(name)

	if val != "" {
		return val
	}

	if len(def) == 0 {
		panic(fmt.Sprintf("Enviromental variable %s is not set", name))
	}

	return def[0]
}

// Get config value as integer
func GetInt(name string, def ...int) int {
	val := Get(name, "")

	if val == "" {
		if len(def) == 0 {
			panic(fmt.Sprintf("Enviromental variable %s is not set", name))
		}

		return def[0]
	}

	res, err := strconv.Atoi(val)
	if err != nil {
		panic(fmt.Sprintf("Enviromental variable %s: %s is not int: %v", name, val, err))
	}

	return res
}

// Get config value as boolean
func GetBool(name string, def ...bool) bool {
	val := Get(name, "")

	if val == "" {
		if len(def) == 0 {
			panic(fmt.Sprintf("Enviromental variable %s is not set", name))
		}

		return def[0]
	}

	if val == "0" || val == "false" {
		return false
	}

	return true
}
