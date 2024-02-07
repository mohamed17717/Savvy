package main

import (
	"fmt"
	"math/rand"
	"time"
)

// generateMatrix creates a matrix of size rows x cols and fills it with random floats.
func generateMatrix(rows, cols int) [][]float64 {
	matrix := make([][]float64, rows)
	for i := range matrix {
		matrix[i] = make([]float64, cols)
		for j := range matrix[i] {
			matrix[i][j] = rand.Float64() // Generates a random float64 [0.0,1.0)
		}
	}
	return matrix
}

func main() {
	rand.Seed(time.Now().UnixNano()) // Ensure different results on each run

	rows, cols := 10000, 10000
	matrix := generateMatrix(rows, cols)

	fmt.Printf("Generated a %d x %d matrix\n", rows, cols)
	// Example of accessing a value
	fmt.Println("Sample value:", matrix[0][0])

	// Caution: Printing the entire matrix will flood your terminal!
	// So, let's not print the whole matrix.
}
