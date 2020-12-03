import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";

import { Observable } from "rxjs";
import { catchError } from "rxjs/operators";

import { handleError } from "./utils";

@Injectable({ providedIn: "root" })
export class CoreService {
    constructor(private httpClient: HttpClient) {}
    getObject<T>(
        url: string,
        alt: any = null,
        operation_string: string = `getObject from ${url}`
    ): Observable<T> {
        return this.httpClient
            .get<T>(url)
            .pipe(catchError(handleError<T>(operation_string, alt)));
    }
    setObject<T>(
        url: string,
        body: T,
        operation_string: string = `setObject to ${url}`
    ): Observable<T> {
        return this.httpClient
            .post<T>(url, body)
            .pipe(catchError(handleError<T>(operation_string)));
    }
}
