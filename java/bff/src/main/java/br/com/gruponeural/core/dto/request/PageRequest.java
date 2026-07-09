package br.com.gruponeural.core.dto.request;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

import com.fasterxml.jackson.annotation.JsonIgnore;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@NoArgsConstructor
public class PageRequest<T> {

    public static final Integer MAX_PAGE_SIZE = 100;
    public static final Integer MAX_OFFSET = 10000;

    private static final Integer DEFAULT_PAGE_NUMBER = 1;
    private static final Integer DEFAULT_PAGE_SIZE = 15;

    @Setter
    private Integer pageNumber;

    @Setter
    private Integer pageSize;

    @Getter
    @Setter
    private T content;

    public Integer getPageNumber() {

        if (pageNumber == null || pageNumber == 0) {
            return DEFAULT_PAGE_NUMBER;
        }

        return pageNumber;

    }

    public Integer getPageSize() {

        if (pageSize == null || pageSize == 0) {
            return DEFAULT_PAGE_SIZE;
        }

        if (pageSize > MAX_PAGE_SIZE) {
            return MAX_PAGE_SIZE;
        }

        return pageSize;

    }

    @JsonIgnore
    @Schema(hidden = true)
    public Integer getOffset() {

        return (getPageNumber() - 1) * getPageSize();

    }

}
