from .base_adapter import FrameworkAdapter

from strands.models.openai import OpenAIModel


class OpenAIAdapter(FrameworkAdapter):

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "default"

    def load_model(self, model_name, model_config = None):
        model_config = model_config or {}
        if model_name:
            model_config["model"] = model_name
        client_args = model_config.pop("client_args", None)
        return OpenAIModel(client_args=client_args,model_config=model_config)

