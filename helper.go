package main

import (
	"fmt"
	"math"
	"math/rand"
	"strings"
	"time"

	"github.com/brianvoe/gofakeit/v6"
)

type User struct {
	Username    string    `json:"username"`
	FirstName   string    `json:"first_name"`
	LastName    string    `json:"last_name"`
	Email       string    `json:"email"`
	Password    string    `json:"password"`
	IsSuperuser bool      `json:"is_superuser"`
	IsStaff     bool      `json:"is_staff"`
	IsActive    bool      `json:"is_active"`
	LastLogin   time.Time `json:"last_login"`
	DateJoined  time.Time `json:"date_joined"`
}

var names_map = map[string]map[string][]string{
	"yoruba": {
		"f": {"Ade", "Olu", "Damilola", "Ayomide", "Tunde", "Sola", "Bolaji", "Funke", "Kehinde", "Taiwo"},
		"l": {"Adeyemi", "Olawale", "Adebayo", "Ogunleye", "Balogun", "Ojo", "Ajayi", "Olatunji"},
	},
	"igbo": {
		"f": {"Chinedu", "Emeka", "Ifeanyi", "Nnamdi", "Obinna", "Chiamaka", "Uche", "Ngozi"},
		"l": {"Okafor", "Okoye", "Eze", "Nwankwo", "Onyekachi", "Nwoye"},
	},
	"hausa": {
		"f": {"Musa", "Sadiq", "Abdul", "Amina", "Zainab", "Usman", "Sule", "Fatima"},
		"l": {"Abdullahi", "Sadiq", "Mohammed", "Bello", "Suleiman", "Lawal", "Ibrahim"},
	},
}

type Property struct {
	Title        string     `json:"title"`
	Description  string     `json:"description"`
	PropertyType string     `json:"property_type"`
	Purpose      string     `json:"purpose"`
	Status       string     `json:"status"`
	Address      string     `json:"address"`
	City         string     `json:"city"`
	State        string     `json:"state"`
	ZipCode      string     `json:"zip_code"`
	Latitude     float64    `json:"latitude"`
	Longitude    float64    `json:"longitude"`
	Bedrooms     int        `json:"bedrooms"`
	Bathrooms    int        `json:"bathrooms"`
	AreaSqft     float64    `json:"area_sqft"`
	Price        float64    `json:"price"`
	PlatformFee  float64    `json:"platform_fee"`
	NetAmount    float64    `json:"net_amount"`
	RentDuration int        `json:"rent_duration_months"`
	Amenities    []string   `json:"amenities"`
	MainImage    string     `json:"main_image"`
	Image1       string     `json:"image_1"`
	Image2       string     `json:"image_2"`
	Image3       string     `json:"image_3"`
	Image4       string     `json:"image_4"`
	Image5       string     `json:"image_5"`
	IsFeatured   bool       `json:"is_featured"`
	Views        int        `json:"views"`
	OwnerId      string     `json:"owner_id"`
	CreatedAt    time.Time  `json:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at"`
	PublishedAt  *time.Time `json:"published_at"`
	SalePrice    *float64   `json:"sale_price"`
	SoldAt       *time.Time `json:"sold_at"`
	RentedToID   *int       `json:"rented_to_id"`
	SoldToID     *int       `json:"sold_to_id"`
}

var propertyTypes = []string{
	"apartment",
	"house",
	"villa",
	"penthouse",
	"studio",
	"duplex",
	"office",
	"land",
	"commercial",
}

var purposes = []string{"rent", "sale"}

var amenitiesList = []string{
	"pool",
	"gym",
	"parking",
	"wifi",
	"garden",
	"elevator",
	"balcony",
	"security",
	"24-7 electricity",
	"water treatment",
	"borehole",
	"furnished",
	"partially furnished",
	"air conditioning",
	"cctv",
	"gated estate",
	"playground",
	"storage room",
	"servant quarters",
	"generator",
}

var adjectives = []string{
	"Luxury",
	"Spacious",
	"Modern",
	"Executive",
	"Newly Built",
	"Fully Furnished",
	"Affordable",
	"Exclusive",
	"Premium",
	"Well Finished",
	"Serviced",
	"Smart",
	"Elegant",
	"Secure",
	"Prime",
	"Stylish",
}

var cities = map[string][]string{
	"FCT": {
		"Asokoro",
		"Maitama",
		"Wuse",
		"Wuse 2",
		"Garki",
		"Gwarinpa",
		"Jabi",
		"Utako",
		"Kubwa",
		"Guzape",
		"Lugbe",
		"Gwagwalada",
	},
	"Lagos": {
		"Victoria Island",
		"Lekki Phase 1",
		"Lekki",
		"Ikoyi",
		"Ajah",
		"Magodo",
		"Yaba",
		"Ikeja",
		"Surulere",
	},
	"Rivers": {
		"Port Harcourt",
		"GRA",
		"Rumuola",
		"Rumuokoro",
	},
	"Oyo": {
		"Ibadan",
		"Bodija",
		"Oluyole",
	},
	"Kano": {
		"Kano",
		"Nassarawa",
	},
	"Enugu": {
		"Independence Layout",
		"New Haven",
		"Enugu",
	},
	"Kaduna": {
		"Kaduna North",
		"Kaduna South",
	},
}

var featuredCount = 0

const maxFeatured = 15

const total_users = 500

const total_properties = 5000

func RandomSubset(slice []string, n int) []string {
	if n >= len(slice) {
		return slice
	}
	result := make([]string, 0, n)
	perm := rand.Perm(len(slice))
	for i := range n {
		result = append(result, slice[perm[i]])
	}
	return result
}

func roundTo(value float64, unit float64) float64 {
	return math.Round(value/unit) * unit
}

func pricePerSqft(ptype, purpose string) float64 {
	if purpose == "rent" {
		switch ptype {
		case "studio":
			return gofakeit.Float64Range(800, 1500)
		case "apartment":
			return gofakeit.Float64Range(1200, 2500)
		case "duplex":
			return gofakeit.Float64Range(2000, 3500)
		case "villa", "penthouse":
			return gofakeit.Float64Range(3000, 5000)
		case "office", "shop":
			return gofakeit.Float64Range(1500, 4000)
		}
	} else { // SALE
		switch ptype {
		case "apartment":
			return gofakeit.Float64Range(80_000, 200_000)
		case "duplex":
			return gofakeit.Float64Range(120_000, 300_000)
		case "villa", "penthouse":
			return gofakeit.Float64Range(200_000, 450_000)
		case "house":
			return gofakeit.Float64Range(100_000, 250_000)
		case "land":
			return gofakeit.Float64Range(50_000, 150_000)
		case "office", "commercial":
			return gofakeit.Float64Range(150_000, 400_000)
		}
	}
	return 100_000
}

func GenerateTitle(ptype string, bedrooms int, city string, sqft float64) string {
	adjective := gofakeit.RandomString(adjectives)
	switch ptype {
	case "office", "commercial":
		return fmt.Sprintf("%s %0.5v SF %s in %s", adjective, sqft, strings.Title(ptype), city)
	case "land":
		return fmt.Sprintf("%0.5v SF %s in %s", sqft, strings.Title(ptype), city)
	default:
		return fmt.Sprintf("%s %dBR %s in %s", adjective, bedrooms, strings.Title(ptype), city)
	}
}
