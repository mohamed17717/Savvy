def only_fields(serializer_class):
    model = serializer_class.Meta.model

    serializer_fields = set(serializer_class().get_fields().keys())
    model_fields = set([f.name for f in model._meta.fields])

    return serializer_fields & model_fields
