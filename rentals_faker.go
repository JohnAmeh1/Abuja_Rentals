package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"runtime"
	"strings"
	"sync"
	"time"

	"math/rand"

	"github.com/brianvoe/gofakeit/v6"
	"github.com/jackc/pgx/v5"
)

var user_ids = []string{}

func FakeProperty() Property {
	ptype := gofakeit.RandomString(propertyTypes)
	purpose := gofakeit.RandomString(purposes)
	status := "available"

	var bedrooms int
	switch ptype {
	case "studio":
		bedrooms = 1
	case "apartment":
		bedrooms = gofakeit.Number(1, 4)
	case "duplex":
		bedrooms = gofakeit.Number(3, 6)
	case "villa", "penthouse":
		bedrooms = gofakeit.Number(4, 8)
	case "house":
		bedrooms = gofakeit.Number(2, 5)
	default:
		bedrooms = 0
	}

	bathrooms := bedrooms
	if bedrooms > 0 {
		bathrooms = gofakeit.Number(bedrooms, bedrooms+2)
	}

	var area float64
	switch ptype {
	case "studio":
		area = gofakeit.Float64Range(400, 700)
	case "apartment":
		area = gofakeit.Float64Range(700, 1800)
	case "duplex", "villa", "penthouse":
		area = gofakeit.Float64Range(2000, 5000)
	case "office", "commercial":
		area = gofakeit.Float64Range(1500, 10000)
	case "land":
		area = gofakeit.Float64Range(2000, 10000)
	default:
		area = gofakeit.Float64Range(800, 2000)
	}

	pps := pricePerSqft(ptype, purpose)
	price := area * pps

	if bedrooms >= 4 {
		price *= gofakeit.Float64Range(1.1, 1.4)
	}

	if purpose == "sale" {
		price = roundTo(price, 1_000_000)
	} else {
		price = roundTo(price, 100_000)
	}

	platformFee := price * 0.05
	netAmount := price - platformFee

	amenitiesCount := 2
	if price > 50_000_000 {
		amenitiesCount = gofakeit.Number(6, len(amenitiesList))
	} else if price > 20_000_000 {
		amenitiesCount = gofakeit.Number(4, 6)
	}
	amenities := RandomSubset(amenitiesList, amenitiesCount)

	seed := fmt.Sprintf("%s-%d", ptype, int(price))
	image := fmt.Sprintf("https://picsum.photos/seed/%s/800/600", seed)

	views := gofakeit.Number(20, 80000)

	now := time.Now()
	createdAt := gofakeit.DateRange(now.AddDate(-2, 0, 0), now)

	state := fmt.Sprintf("%v", gofakeit.RandomMapKey(cities))
	city := gofakeit.RandomString(cities[state])
	fmt.Print(".")
	isFeatured := false

	if featuredCount < maxFeatured {
		if v := rand.Intn(100); v == 9 {
			isFeatured = true
			featuredCount++
		}
	}

	return Property{
		Title:        GenerateTitle(ptype, bedrooms, city, area),
		Description:  gofakeit.Paragraph(1, 3, 6, ","),
		PropertyType: ptype,
		Purpose:      purpose,
		Status:       status,
		Address:      gofakeit.Address().Street,
		City:         city,
		State:        state,
		ZipCode:      gofakeit.Zip(),
		Latitude:     gofakeit.Latitude(),
		Longitude:    gofakeit.Longitude(),
		Bedrooms:     bedrooms,
		Bathrooms:    bathrooms,
		AreaSqft:     area,
		Price:        price,
		PlatformFee:  platformFee,
		NetAmount:    netAmount,
		RentDuration: gofakeit.Number(1, 24),
		Amenities:    amenities,
		MainImage:    image,
		Image1:       image,
		Image2:       image,
		Image3:       image,
		Image4:       image,
		Image5:       image,
		Views:        views,
		CreatedAt:    createdAt,
		UpdatedAt:    createdAt,
		PublishedAt:  &createdAt,
		OwnerId:      gofakeit.RandomString(user_ids),
		IsFeatured:   isFeatured,
	}
}

func worker(jobs <-chan int, results chan<- Property, wg *sync.WaitGroup) {
	defer wg.Done()
	for range jobs {
		results <- FakeProperty()
	}
}

func get_user_ids(conn *pgx.Conn) error {
	ctx := context.Background()
	tx, err := conn.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	ids_data, err := tx.Query(ctx, `Select id From auth_user`)
	if err != nil {
		return err
	}
	for ids_data.Next() {
		data_arr, err := ids_data.Values()
		if err != nil {
			break
		}
		user_ids = append(user_ids, fmt.Sprintf("%v", data_arr[0]))
	}
	return tx.Commit(ctx)
}

func clearDatabase(conn *pgx.Conn) error {
	ctx := context.Background()
	tx, err := conn.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	_, err = tx.Exec(ctx, `
	Delete From rentals_payment;
	Delete From rentals_report;
	Delete From rentals_transactions;
	Delete From rentals_proprertyrental;
	Delete From rentals_studentpropertyrental;
	Delete From rentals_propertyownership;
	Delete From rentals_proprertyvisit;
	Delete From rentals_property;
	Delete From student_property;
	Delete From rentals_userprofile USING auth_user WHERE rentals_userprofile.user_id = auth_user.id AND auth_user.username LIKE 'bot%';
	Delete From rentals_wallet;
	Delete From auth_user WHERE username LIKE 'bot%';`)
	
	if err != nil {
		return err
	}

	fmt.Println("Purged Database")

	return tx.Commit(ctx)
}

// func insertBatch(conn *pgx.Conn, batch []Property) error {
// 	ctx := context.Background()
// 	tx, err := conn.Begin(ctx)
// 	if err != nil {
// 		return err
// 	}
// 	defer tx.Rollback(ctx)

// 	for _, p := range batch {
// 		amenitiesJSON, _ := json.Marshal(p.Amenities)
// 		_, err := tx.Exec(ctx,
// 			`INSERT INTO rentals_property (
// 				title, description, property_type, purpose, status, address, city, state, zip_code,
// 				latitude, longitude, bedrooms, bathrooms, area_sqft, price,
// 				platform_fee, net_amount, rent_duration_months, amenities,
// 				main_image, image_1, image_2, image_3, image_4, image_5,
// 				is_featured, views, created_at, updated_at,
// 				published_at, sale_price, sold_at, rented_to_id, sold_to_id, owner_id
// 			) VALUES (
// 				$1,$2,$3,$4,$5,$6,$7,$8,$9,
// 				$10,$11,$12,$13,$14,$15,
// 				$16,$17,$18,$19,
// 				$20,$21,$22,$23,$24,$25,
// 				$26,$27,$28,$29,
// 				$30,$31,$32,$33,$34,$35
// 			)`,
// 			p.Title, p.Description, p.PropertyType, p.Purpose, p.Status, p.Address, p.City, p.State, p.ZipCode,
// 			p.Latitude, p.Longitude, p.Bedrooms, p.Bathrooms, p.AreaSqft, p.Price,
// 			p.PlatformFee, p.NetAmount, p.RentDuration, amenitiesJSON,
// 			p.MainImage, p.Image1, p.Image2, p.Image3, p.Image4, p.Image5,
// 			p.IsFeatured, p.Views, p.CreatedAt, p.UpdatedAt,
// 			p.PublishedAt, p.SalePrice, p.SoldAt, p.RentedToID, p.SoldToID, p.OwnerId,
// 		)
// 		if err != nil {
// 			return err
// 		}
// 	}
// 	fmt.Println("__completed__")

// 	return tx.Commit(ctx)
// }

func insertBatch(conn *pgx.Conn, batch []Property) error {
	ctx := context.Background()

	var (
		query  strings.Builder
		values []interface{}
	)

	query.WriteString(`
		INSERT INTO rentals_property (
			title, description, property_type, purpose, status,
			address, city, state, zip_code,
			latitude, longitude,
			bedrooms, bathrooms, area_sqft,
			price, platform_fee, net_amount,
			rent_duration_months, amenities,
			main_image, image_1, image_2, image_3, image_4, image_5,
			is_featured, views, created_at, updated_at, owner_id
		) VALUES
	`)

	arg := 1

	for i, p := range batch {
		if i > 0 {
			query.WriteString(",")
		}

		query.WriteString("(")
		for j := range 30 {
			query.WriteString(fmt.Sprintf("$%d", arg))
			arg++
			if j < 29 {
				query.WriteString(",")
			}
		}
		query.WriteString(")")

		amenitiesJSON, _ := json.Marshal(p.Amenities)

		values = append(values,
			p.Title, p.Description, p.PropertyType, p.Purpose, p.Status,
			p.Address, p.City, p.State, p.ZipCode,
			p.Latitude, p.Longitude,
			p.Bedrooms, p.Bathrooms, p.AreaSqft,
			p.Price, p.PlatformFee, p.NetAmount,
			p.RentDuration, amenitiesJSON,
			p.MainImage, p.Image1, p.Image2, p.Image3, p.Image4, p.Image5,
			p.IsFeatured, p.Views, p.CreatedAt, p.UpdatedAt, p.OwnerId,
		)
	}

	_, err := conn.Exec(ctx, query.String(), values...)
	return err
}

func main() {
	rand.Seed(time.Now().UnixNano())
	gofakeit.Seed(time.Now().UnixNano())

	// connStr := "postgresql://postgres.xtcsrbcalaqolnzhhugw:S6cjBxrbYc9WMBo3@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
	connStr := "postgresql://postgres:cr7ndozilGJDMA@localhost:5432/abuja_rentals"
	conn, err := pgx.Connect(context.Background(), connStr)
	if err != nil {
		log.Fatal("Unable to connect:", err)
	}
	defer conn.Close(context.Background())

	clearDatabase(conn)
	fake_users(conn, total_users)

	err = get_user_ids(conn)

	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Users Done starting houses")

	CPUCount := runtime.NumCPU()

	jobs := make(chan int, total_properties)
	results := make(chan Property, total_properties)

	var wg sync.WaitGroup

	for range CPUCount {
		wg.Add(1)
		go worker(jobs, results, &wg)
	}

	for i := range total_properties {
		jobs <- i
	}
	close(jobs)

	go func() {
		wg.Wait()
		close(results)
	}()

	var batch []Property
	batchSize := 500
	for prop := range results {
		batch = append(batch, prop)
		if len(batch) == batchSize {
			fmt.Println("Batch ready to send:", len(batch))
			err := insertBatch(conn, batch)
			if err != nil {
				log.Println("Error inserting batch:", err)
			} else {
				fmt.Println("✅ Batch inserted:", len(batch))
			}
			batch = batch[:0]
		}
	}

	if len(batch) > 0 {
		fmt.Println("Final batch ready to send:", len(batch))
		err := insertBatch(conn, batch)
		if err != nil {
			log.Println("Error inserting batch:", err)
		} else {
			fmt.Println("✅ Batch inserted:", len(batch))
		}
	}

	fmt.Println("✅ Finished generating 5000 fake properties concurrently.")
}
