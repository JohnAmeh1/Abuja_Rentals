package main

import (
	"context"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/brianvoe/gofakeit/v6"
	"github.com/jackc/pgx/v5"
)

func FakeUser() User {

	fn := fmt.Sprint(gofakeit.RandomMapKey(names_map))

	firstName := gofakeit.RandomString(names_map[fn]["f"])
	lastName := gofakeit.RandomString(names_map[fn]["l"])

	username := fmt.Sprintf(
		"%s.%s%d",
		strings.ToLower(firstName),
		strings.ToLower(lastName),
		gofakeit.Number(100, 999999),
	)

	email := fmt.Sprintf("%s@gmail.com", username)

	now := time.Now()
	dateJoined := gofakeit.DateRange(now.AddDate(-3, 0, 0), now)
	lastLogin := gofakeit.DateRange(dateJoined, now)

	password := gofakeit.Password(true, true, true, false, false, 10)

	fmt.Print(".")

	return User{
		FirstName:   firstName,
		LastName:    lastName,
		Username:   "bot_" + username,
		Email:       email,
		DateJoined:  dateJoined,
		LastLogin:   lastLogin,
		Password:    password,
		IsSuperuser: false,
		IsStaff:     false,
		IsActive:    true,
	}
}

func fake_users(conn *pgx.Conn, total int) {
	users := make([]User, total)

	for i := range total {
		users[i] = FakeUser()
	}

	err := insertUsers(conn, users)
	if err != nil {
		log.Println("Error inserting users:", err)
	} else {
		fmt.Println("✅", len(users), " Users Generated:")
	}

}
func insertUsers(conn *pgx.Conn, users []User) error {
	ctx := context.Background()

	var (
		query  strings.Builder
		values []interface{}
	)

	query.WriteString(`
		INSERT INTO auth_user (
			username,
			first_name,
			last_name,
			email,
			password,
			is_superuser,
			is_staff,
			is_active,
			date_joined,
			last_login
		) VALUES
	`)

	arg := 1

	for i, u := range users {
		if i > 0 {
			query.WriteString(",")
		}

		query.WriteString("(")
		for j := 0; j < 10; j++ {
			query.WriteString(fmt.Sprintf("$%d", arg))
			arg++
			if j < 9 {
				query.WriteString(",")
			}
		}
		query.WriteString(")")

		values = append(values,
			u.Username,
			u.FirstName,
			u.LastName,
			u.Email,
			u.Password,
			u.IsSuperuser,
			u.IsStaff,
			u.IsActive,
			u.DateJoined,
			u.LastLogin,
		)
	}

	_, err := conn.Exec(ctx, query.String(), values...)
	return err
}
