package br.com.gruponeural.core.dto.response;

import java.util.List;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PageResponse<T> {

    private Integer totalPages;
    private Integer pageNumber;
    private Integer pageSize;
    private Long totalItems;
    private List<T> items;

}
