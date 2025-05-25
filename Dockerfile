FROM jupyter/minimal-notebook

# Set working directory
WORKDIR /home/jovyan/work

# Copy your environment file
COPY environment.yml .

# Create the environment (name must match conda activate below)
RUN conda env create -f environment.yml && \
    conda clean -a

# Activate environment by default in every shell
RUN echo "conda activate joseph_rich_blog" >> ~/.bashrc

# Copy notebooks and other files
COPY . .

# Use the environment in Jupyter
RUN echo "c.NotebookApp.kernel_spec_manager_class = 'nb_conda_kernels.CondaKernelSpecManager'" >> /etc/jupyter/jupyter_notebook_config.py

# Install the IPython kernel so the env appears in Jupyter
RUN conda install -n joseph_rich_blog -y ipykernel && \
    conda run -n joseph_rich_blog python -m ipykernel install --user --name=joseph_rich_blog --display-name "Python (joseph_rich_blog)"
