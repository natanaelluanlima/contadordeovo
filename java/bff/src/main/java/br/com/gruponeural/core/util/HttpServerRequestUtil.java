package br.com.gruponeural.core.util;

import io.vertx.core.http.HttpServerRequest;

public class HttpServerRequestUtil {

    static public String obterIP(HttpServerRequest request) {

        String[] headers = {
            "X-Forwarded-For",
            "X-Real-IP",
            "CF-Connecting-IP",
            "True-Client-IP"
        };

        for (String header : headers) {

            String value = request.getHeader(header);

            if (value != null && !value.isBlank()) {
                return value.split(",")[0].trim();

            }

        }

        return request.remoteAddress().host();

    }

    static public String obterUserAgent(HttpServerRequest request) {

        return request.getHeader("User-Agent");

    }

}
