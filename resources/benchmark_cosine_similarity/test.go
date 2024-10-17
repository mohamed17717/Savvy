package main

import (
	"fmt"
	"math/rand"
	"time"
	"math"
	"sync"
)

// Vector represents a simple vector of floats.
type Vector []float64

// dot calculates the dot product of two vectors.
func dot(v1, v2 Vector) float64 {
	sum := 0.0
	for i := range v1 {
		sum += v1[i] * v2[i]
	}
	return sum
}

// magnitude calculates the magnitude (Euclidean norm) of a vector.
func magnitude(v Vector) float64 {
	sum := 0.0
	for _, value := range v {
		sum += value * value
	}
	return math.Sqrt(sum)
}

// cosineSimilarity calculates the cosine similarity between two vectors.
func cosineSimilarity(v1, v2 Vector) float64 {
	return dot(v1, v2) / (magnitude(v1) * magnitude(v2))
}

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

// calculatePairwiseSimilarity calculates cosine similarities for all pairs of vectors concurrently.
func calculatePairwiseSimilarity(vectors [][]float64) []float64 {
	var wg sync.WaitGroup
	similarities := make([]float64, len(vectors)/2)

	for i := 0; i < len(vectors); i += 2 {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			similarities[i/2] = cosineSimilarity(vectors[i], vectors[i+1])
		}(i)
	}

	wg.Wait()
	return similarities
}

func main() {
	// vectors := []Vector{
	// 	{1, 2, 3},
	// 	{4, 5, 6},
	// 	{1, 1, 1},
	// 	{2, 2, 2},
	// }

	rand.Seed(time.Now().UnixNano()) // Ensure different results on each run

	rows, cols := 20000, 10000
	matrix := generateMatrix(rows, cols)

	// similarities :=
	calculatePairwiseSimilarity(matrix)
	fmt.Println("Cosine Similarities DONE")
	// similarities)
}
