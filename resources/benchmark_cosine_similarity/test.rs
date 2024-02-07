use ndarray::{Array2, Axis};
use ndarray_rand::rand_distr::Uniform;
use ndarray_rand::RandomExt;
use rayon::prelude::*;

fn cosine_similarity(matrix: &Array2<f64>) -> Array2<f64> {
    let norms = matrix.map_axis(Axis(1), |row| row.dot(&row).sqrt());
    let nrows = matrix.nrows();
    let ncols = matrix.ncols();
    let results: Vec<Vec<f64>> = (0..nrows).into_par_iter().map(|i| {
        let row_a = matrix.row(i);
        (0..ncols).into_iter().map(|j| {
            if i == j {
                1.0
            } else {
                let row_b = matrix.row(j);
                row_a.dot(&row_b) / (norms[i] * norms[j])
            }
        }).collect()
    }).collect();

    // Convert Vec<Vec<f64>> to Array2<f64>
    let similarity_matrix = Array2::from_shape_vec((nrows, ncols), results.into_iter().flatten().collect()).unwrap();
    similarity_matrix
}

fn main() {
    let n = 1000; // Use a smaller size for testing; adjust as needed.
    let matrix = Array2::random((n, n), Uniform::new(0., 1.));
    let similarity_matrix = cosine_similarity(&matrix);
    println!("Calculated cosine similarity for the matrix.");
    // Note: Printing the entire matrix might not be practical.
}
