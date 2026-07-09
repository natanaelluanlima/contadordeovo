package br.com.gruponeural.core.util;

import java.util.List;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.datatype.jdk8.Jdk8Module;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.fasterxml.jackson.module.paramnames.ParameterNamesModule;

public class JsonUtil {

    public static ObjectMapper getMapper() {

        return JsonMapper
            .builder()
            .addModule(new ParameterNamesModule())
            .addModule(new Jdk8Module())
            .addModule(new JavaTimeModule())
            .build()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    }

    @SuppressWarnings("unchecked")
    public static String toJson(Object object) {

        if (object == null) {
            return "null";
        }

        String json = object.getClass().getName() + ": ";

        if (object instanceof String) {

            json = json.concat("\"");
            json = json.concat((String) object);
            json = json.concat("\"");

        } else if (object instanceof List) {

            json = json.concat("[");
            json = json.concat(JsonUtil.toJson((List<Object>) object));
            json = json.concat("]");

        } else {

            try {

                json = json.concat(JsonUtil.getMapper().writerWithDefaultPrettyPrinter().writeValueAsString(object));

            } catch (JsonProcessingException e) {

                System.out.println(e);

                json = json.concat(object.toString());

            }

        }

        return json;

    }

    @SuppressWarnings("unchecked")
    public static String toJsonb(Object object) {

        if (object == null) {
            return "null";
        }

        if (object instanceof String) {
            return "\"" + object + "\"";
        }

        if (object instanceof List) {
            return JsonUtil.toJson((List<Object>) object);
        }

        try {
            return JsonUtil.getMapper().writeValueAsString(object);
        } catch (JsonProcessingException e) {
            System.err.println("Erro ao serializar objeto: " + e.getMessage());
            return null;
        }

    }

    public static String toJson(List<Object> listObject) {

        List<String> listJson = listObject.stream().map((item) -> JsonUtil.toJson(item)).toList();
        return ListUtil.toString(listJson);

    }

}
