!* Copyright (c) 1998, NVIDIA CORPORATION.  All rights reserved.
!*
!* Licensed under the Apache License, Version 2.0 (the "License");
!* you may not use this file except in compliance with the License.
!* You may obtain a copy of the License at
!*
!*     http://www.apache.org/licenses/LICENSE-2.0
!*
!* Unless required by applicable law or agreed to in writing, software
!* distributed under the License is distributed on an "AS IS" BASIS,
!* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
!* See the License for the specific language governing permissions and
!* limitations under the License.

*   Scope of private variables
*   DO

	program test
        implicit none
	integer i, n
	parameter(n = 10)
	integer j, k, aa(n)
	integer result(n+2), expect(n+2)
	j = 99
	k = 2
	call sub(j, k, n, aa)
	result(1) = j
	result(2) = k
	do i = 1, n
	    result(i+2) = aa(i)
	enddo

	data expect/100, 2,			! j & k after call
     +     3, 4, 5, 6, 7, 8, 9, 10, 11, 12/	! aa after call
	call check(result, expect, n+2)
	end
	subroutine sub(j, k, n, aa)
	integer aa(n)
!$omp do, private(j), firstprivate(k)
	do i = 1, n
	    j = k		! j & k are not the dummy variables
	    k = k + 1
	    aa(i) = k
	enddo
!$omp enddo
	j = j + 1
	end
