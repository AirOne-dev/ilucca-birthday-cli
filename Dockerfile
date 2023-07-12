FROM gitlab-registry.easyflirt.com/global/docker-images/python as build
WORKDIR /scripts
ENTRYPOINT ["poetry"]
CMD ["run", "server"]
COPY poetry.* pyproject.toml ./
RUN poetry install --no-root
COPY . .
RUN poetry install