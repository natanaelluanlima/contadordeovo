package br.com.gruponeural.core.util;

import java.util.List;

import br.com.gruponeural.core.dto.response.PageResponse;

public final class PageResponseUtil {

    private PageResponseUtil() {
    }

    public static <T> PageResponse<T> of(Integer pageNumber, Integer pageSize, Long totalItems, List<T> items) {

        PageResponse<T> page = new PageResponse<>();
        page.setPageNumber(pageNumber);
        page.setPageSize(pageSize);
        page.setTotalItems(totalItems);
        page.setItems(items);

        if (totalItems == null || pageSize == null || pageSize <= 0) {
            page.setTotalPages(0);
            return page;
        }

        int totalPages = (int) Math.ceil(totalItems.doubleValue() / pageSize.doubleValue());
        page.setTotalPages(totalPages);
        return page;

    }

}

