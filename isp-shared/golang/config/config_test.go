package config

import (
	"os"
	"testing"
)

func TestGet(t *testing.T) {
	os.Setenv("UTILS_ENV_TEST", "Set")

	if env := Get("UTILS_ENV_TEST"); env != "Set" {
		t.Errorf(`Expected "Set", got "%s"`, env)
	}

	env := Get("UTILS_ENV_TEST", "Hello")
	if env != "Set" {
		t.Errorf(`Expected not "Set", got "%s"`, env)
	}

	env = Get("UTILS_ENV_NOT_SET", "Goodbye")
	if env != "Goodbye" {
		t.Errorf(`Expected "Goodbye", got "%s"`, env)
	}

	os.Setenv("UTILS_ENV_TEST_INT", "5")
	if env := Get("UTILS_ENV_TEST_INT"); env != "5" {
		t.Errorf(`Expected "5", got "%s"`, env)
	}
}

func TestGetInt(t *testing.T) {
	if env := GetInt("UTILS_ENV_TEST_INT"); env != 5 {
		t.Errorf(`Expected 5 (Integer), got %v`, env)
	}

	if env := GetInt("UTILS_ENV_TEST_INT_NOT_SET", 7); env != 7 {
		t.Errorf(`Expected 7 (Integer), got %v`, env)
	}
}

func TestGetBool(t *testing.T) {
	if env := GetBool("UTILS_TEST_BOOL_NOT_SET", true); env != true {
		t.Errorf(`Expected true (bool), got %v`, env)
	}

	if env := GetBool("UTILS_ENV_TEST_BOOL_FALSE"); env != false {
		t.Errorf(`Expected false (bool), got %v`, env)
	}

	if env := GetBool("UTILS_ENV_TEST_BOOL_TRUE"); env != true {
		t.Errorf(`Expected true (bool), got %v`, env)
	}
}

func catchPanic(t *testing.T, f func()) {
	defer func() { recover() }()
	f()
	t.Errorf("should have panicked")
}

func TestPanics(t *testing.T) {
	catchPanic(t, func() {
		_ = Get("UTILS_ENV_NOT_SET")
	})

	catchPanic(t, func() {
		_ = GetInt("UTILS_ENV_TEST_INT_NOT_SET")
	})

	catchPanic(t, func() {
		_ = GetInt("UTILS_ENV_TEST_BAD_INT", 1)
	})

	catchPanic(t, func() {
		_ = GetBool("UTILS_ENV_TEST_BOOL_NOT_SET")
	})
}

func TestDotEnv(t *testing.T) {
	if env := Get("UTILS_ENV_TEST_DOT_ENV"); env != "from_dot_env" {
		t.Errorf(`Expected "from_dot_env" (from .env file), got %v`, env)
	}

	if env := Get("UTILS_ENV_TEST_DOT_ENV", "Attempt to override"); env != "from_dot_env" {
		t.Errorf(`Expected "from_dot_env" (from .env file), got %v`, env)
	}
}
