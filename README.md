# Joseph Rich – Blog Code Repository

This repository contains the code and content that accompanies the blog posts on [joseph-rich.com](https://joseph-rich.com).

## 📂 Repository Structure

- `notebooks/` – Jupyter notebooks for each post, organized by topic or series.  
  Use these to follow along with the analyses and examples in each blog post.

- `articles/` – Markdown or plain text versions of each blog post, for archival and reference purposes.

- `environment.yml` – The Conda environment file needed to run the notebooks locally.

## 🚀 Running the Notebooks

### Option 1: Using Conda (recommended for local development)

Create the environment:

```bash
conda env create -f environment.yml
conda activate joseph_rich_blog
jupyter notebook
```

### Options 2: Using Google Colab
You can also run the notebooks directly in Google Colab. Just open the desired notebook file from the `notebooks/` directory in Colab with the Colab link.

### Option 3: Using Docker
If you prefer to run the notebooks in a containerized environment, you can use Docker:
```bash
docker build -t joseph_rich_blog .
docker run -p 8888:8888 -v "$(pwd):/home/jovyan/work" joseph_rich_blog
```
Then open your browser to `http://localhost:8888` to access the Jupyter interface.