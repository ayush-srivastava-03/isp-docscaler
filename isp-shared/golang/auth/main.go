package auth

// GRPC interceptor to add user information and
// access level to context of request

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"isp/config"
	"isp/deployment"
	"isp/log"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

var JWT_HEADER = config.Get("JWT_HEADER", "authorization")

type Role string

const (
	AdminRole     Role = "admin"
	ManagerRole   Role = "manager"
	DeveloperRole Role = "developer"
	UserRole      Role = "user"
	AnonymousRole Role = "anonymous"
)

const CTX_USER_NAMESPACE = "ISPUser"

type RoleMap map[Role][]string

type User struct {
	UserId string   `json:"userId"`
	Groups []string `json:"groups"`
	Role   Role     `json:"role"`
}

type Interceptor struct {
	Roles RoleMap `json:"roleMap"`
}

type jwtPayload struct {
	UserId string   `json:"sub"`
	Groups []string `json:"groups"`
}

func Create(roles RoleMap) *Interceptor {
	return &Interceptor{
		Roles: roles,
	}
}

func CreateFromJson(src string) (*Interceptor, error) {
	var m RoleMap
	if err := json.Unmarshal([]byte(src), &m); err != nil {
		return nil, fmt.Errorf("roles json parsing error: %v", err)
	}

	return Create(m), nil
}

func (ir *Interceptor) decodeAuthHeader(src string) (*jwtPayload, error) {
	v := strings.Split(src, " ")
	if len(v) != 2 || v[0] != "Bearer" {
		return nil, fmt.Errorf("invalid token format (1)")
	}

	// Get middle part, which contains payload
	// We don't need to validate signature or method, as it
	// should be already validated by envoy
	t := strings.Split(v[1], ".")
	if len(t) != 3 {
		return nil, fmt.Errorf("invalid token format (2)")
	}

	token, err := base64.RawURLEncoding.DecodeString(t[1])
	if err != nil {
		return nil, fmt.Errorf("base64 decode: %v", err)
	}

	var info jwtPayload
	if err := json.Unmarshal(token, &info); err != nil {
		return nil, fmt.Errorf("unmarshal json: %v", err)
	}

	return &info, nil
}

// Mix user information and roles to request context
func (ir *Interceptor) Unary(ctx context.Context, req interface{},
	info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	// For darksite deployments we're using simple authentication (see envoy settings)
	// All users are admins
	if deployment.IsDarkSite() {
		return handler(context.WithValue(ctx, CTX_USER_NAMESPACE, User{
			UserId: "darksite_user",
			Role:   AdminRole,
		}), req)
	}

	// Get User Information
	meta, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Errorf(codes.Internal, "failed to get metadata of request")
	}

	// Default is anonymous
	userCtx := context.WithValue(ctx, CTX_USER_NAMESPACE, User{
		UserId: "anonymous",
		Role:   AnonymousRole,
	})

	jwt := meta.Get(JWT_HEADER)
	if len(jwt) == 0 {
		log.Msg.Warnf("Detected anonymous request to %s", info.FullMethod)
	} else {
		payload, err := ir.decodeAuthHeader(jwt[0])
		if err != nil {
			log.Msg.Errorf("failed to decode jwt token: %v. Fallback to anonymous user", err)
		} else {
			userCtx = context.WithValue(ctx, CTX_USER_NAMESPACE, User{
				UserId: payload.UserId,
				Groups: payload.Groups,
				Role:   ir.getRole(payload.Groups),
			})
		}
	}

	return handler(userCtx, req)
}

func GetUser(ctx context.Context) (*User, error) {
	user, ok := ctx.Value(CTX_USER_NAMESPACE).(User)
	if !ok {
		return nil, fmt.Errorf("user is not found in context")
	}

	return &user, nil
}

func (ir *Interceptor) getRole(groups []string) Role {
	res := AnonymousRole

	order := []Role{UserRole, DeveloperRole, ManagerRole, AdminRole}
	for _, role := range order {
		if len(ir.Roles[role]) == 0 {
			continue
		}

		for _, ug := range groups {
			for _, g := range ir.Roles[role] {
				if ug == g {
					res = role
				}
			}
		}
	}

	return res
}
