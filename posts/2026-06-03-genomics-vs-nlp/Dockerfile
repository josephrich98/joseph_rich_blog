FROM jupyter/minimal-notebook

# Set working directory
WORKDIR /home/jovyan/work

# Copy the environment spec (environment.yml pins Python + pip, then installs
# the pip packages listed in requirements.txt)
COPY environment.yml requirements.txt .

# Create the environment (name must match conda activate below)
RUN conda env create -f environment.yml && \
    conda clean -a

# Activate environment by default in every shell
RUN echo "conda activate genomics-vs-nlp" >> ~/.bashrc

# Copy the rest of this post directory (notebook, main.md, figures/, data/, scripts/)
COPY . .

# Let Jupyter discover conda environments as kernels
RUN conda install -n base -y nb_conda_kernels && \
    echo "c.NotebookApp.kernel_spec_manager_class = 'nb_conda_kernels.CondaKernelSpecManager'" >> /etc/jupyter/jupyter_notebook_config.py

# Install the IPython kernel so the env appears in Jupyter
RUN conda install -n genomics-vs-nlp -y ipykernel && \
    conda run -n genomics-vs-nlp python -m ipykernel install --user --name=genomics-vs-nlp --display-name "Python (genomics-vs-nlp)"

# Jupyter listens on 8888 (the base image's default CMD starts the server)
EXPOSE 8888
