package br.com.gruponeural.core.util;

public class StringUtil {

    public static String empty() {

        return "";
    }

    public static Boolean isEmpty(String value) {

        return value == null || value.trim().isEmpty();
    }

    public static String ifThen(Boolean condition, String valueTrue, String valueFalse) {

        return condition ? valueTrue : valueFalse;

    }

    public static String ifThen(Boolean condition, String valueTrue) {

        return condition ? valueTrue : StringUtil.empty();

    }

    public static String ifNotEmpty(String value, String valueTrue) {

        return ifThen(!isEmpty(value), valueTrue);

    }

}
